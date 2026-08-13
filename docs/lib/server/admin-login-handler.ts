import { NextResponse } from 'next/server';
import { parseAdminDestination } from './admin-destination';

export type AdminLoginErrorCode =
  | 'invalid_request'
  | 'invalid'
  | 'rate'
  | 'config'
  | 'limiter'
  | 'server';

type AdminReadinessResult =
  | { available: true }
  | {
      available: false;
      reason:
        | 'credentials_missing'
        | 'distributed_limiter_missing'
        | 'redis_configuration_invalid';
    };

type AdminAuthenticationResult =
  | { ok: true }
  | {
      ok: false;
      reason:
        | 'invalid'
        | 'credentials_missing'
        | 'distributed_limiter_missing'
        | 'redis_configuration_invalid';
    };

type AdminRateLimitResult =
  | { allowed: true }
  | {
      allowed: false;
      reason: 'rate_limited' | 'distributed_limiter_required';
      retryAfterMs?: number;
    };

type AdminSessionCookie = {
  name: string;
  value: string;
  options: Parameters<NextResponse['cookies']['set']>[2];
};

export type AdminLoginObservation = {
  requestId: string;
  startedAt: number;
  statusCode: number;
  authSuccess?: boolean;
  errorMessage?: string;
};

export type AdminLoginDependencies = {
  requestId: string;
  getReadiness(): AdminReadinessResult;
  checkRateLimit(request: Request): AdminRateLimitResult;
  authenticate(password: string): Promise<AdminAuthenticationResult>;
  createSessionCookie(): Promise<AdminSessionCookie>;
  recordObservation(observation: AdminLoginObservation): Promise<void>;
  now?: () => number;
};

type LoginFailure = {
  code: AdminLoginErrorCode;
  message: string;
  status: 400 | 401 | 429 | 500 | 503;
  retryAfterSeconds?: number;
};

const FAILURE_DETAILS: Record<
  Exclude<AdminLoginErrorCode, 'rate'>,
  Omit<LoginFailure, 'code'>
> = {
  invalid_request: {
    status: 400,
    message: 'The login request was invalid.',
  },
  invalid: {
    status: 401,
    message: 'Invalid admin password.',
  },
  config: {
    status: 503,
    message: 'Admin credentials are not configured.',
  },
  limiter: {
    status: 503,
    message: 'A production-safe distributed login limiter is unavailable.',
  },
  server: {
    status: 500,
    message: 'Admin login operation failed.',
  },
};

function parseQuality(value: string): number | undefined {
  if (!/^(?:0(?:\.\d{0,3})?|1(?:\.0{0,3})?)$/u.test(value)) {
    return undefined;
  }
  const quality = Number(value);
  return Number.isFinite(quality) ? quality : undefined;
}

/**
 * Choose the response representation from explicit media ranges only.
 * Missing or wildcard-only headers remain API-safe JSON defaults.
 */
export function selectAdminLoginResponseMode(
  accept: string | null,
): 'html' | 'json' {
  if (!accept) {
    return 'json';
  }

  let htmlQuality = 0;
  let jsonQuality = 0;
  for (const rawRange of accept.split(',')) {
    const [rawMediaType, ...parameters] = rawRange.split(';');
    const mediaType = rawMediaType?.trim().toLowerCase();
    if (!mediaType || !mediaType.includes('/')) {
      continue;
    }

    let quality = 1;
    let valid = true;
    for (const rawParameter of parameters) {
      const [rawName, rawValue] = rawParameter.split('=', 2);
      if (rawName?.trim().toLowerCase() !== 'q') {
        continue;
      }
      const parsed = parseQuality(rawValue?.trim() ?? '');
      if (parsed === undefined) {
        valid = false;
        break;
      }
      quality = parsed;
    }
    if (!valid) {
      continue;
    }

    if (mediaType === 'text/html' || mediaType === 'application/xhtml+xml') {
      htmlQuality = Math.max(htmlQuality, quality);
    } else if (
      mediaType === 'application/json' ||
      mediaType.endsWith('+json')
    ) {
      jsonQuality = Math.max(jsonQuality, quality);
    }
  }

  return htmlQuality > 0 && htmlQuality >= jsonQuality ? 'html' : 'json';
}

export function buildAdminLoginAction(
  destination: string | null | undefined,
): string {
  const query = new URLSearchParams({ next: parseAdminDestination(destination) });
  return `/api/admin/login?${query.toString()}`;
}

function readinessFailure(
  reason:
    | 'credentials_missing'
    | 'distributed_limiter_missing'
    | 'redis_configuration_invalid',
): LoginFailure {
  const code = reason === 'credentials_missing' ? 'config' : 'limiter';
  return { code, ...FAILURE_DETAILS[code] };
}

function loginPageLocation(
  request: Request,
  code: AdminLoginErrorCode,
  destination: string,
): URL {
  const location = new URL('/admin/login', request.url);
  location.searchParams.set('error', code);
  location.searchParams.set('next', destination);
  return location;
}

function applySharedHeaders(
  response: NextResponse,
  retryAfterSeconds?: number,
): NextResponse {
  response.headers.set('Cache-Control', 'no-store');
  response.headers.set('Vary', 'Accept');
  if (retryAfterSeconds !== undefined) {
    response.headers.set('Retry-After', String(retryAfterSeconds));
  }
  return response;
}

function failureResponse(
  request: Request,
  mode: 'html' | 'json',
  destination: string,
  failure: LoginFailure,
): NextResponse {
  const response =
    mode === 'html'
      ? NextResponse.redirect(
          loginPageLocation(request, failure.code, destination),
          { status: 303 },
        )
      : NextResponse.json(
          { ok: false, code: failure.code, error: failure.message },
          { status: failure.status },
        );
  return applySharedHeaders(response, failure.retryAfterSeconds);
}

function successResponse(
  request: Request,
  mode: 'html' | 'json',
  destination: string,
  sessionCookie: AdminSessionCookie,
): NextResponse {
  const response =
    mode === 'html'
      ? NextResponse.redirect(new URL(destination, request.url), { status: 303 })
      : NextResponse.json({ ok: true, redirect: destination }, { status: 200 });
  response.cookies.set(
    sessionCookie.name,
    sessionCookie.value,
    sessionCookie.options,
  );
  return applySharedHeaders(response);
}

async function observeResponse(
  dependencies: AdminLoginDependencies,
  observation: Omit<AdminLoginObservation, 'requestId'>,
): Promise<void> {
  await Promise.allSettled([
    dependencies.recordObservation({
      requestId: dependencies.requestId,
      ...observation,
    }),
  ]);
}

export async function handleAdminLogin(
  request: Request,
  dependencies: AdminLoginDependencies,
): Promise<NextResponse> {
  const now = dependencies.now ?? (() => performance.now());
  const startedAt = now();
  const mode = selectAdminLoginResponseMode(request.headers.get('accept'));
  const destination = parseAdminDestination(
    new URL(request.url).searchParams.get('next'),
  );

  async function finish(
    response: NextResponse,
    details: { authSuccess?: boolean; errorMessage?: string } = {},
  ): Promise<NextResponse> {
    await observeResponse(dependencies, {
      startedAt,
      statusCode: response.status,
      authSuccess: details.authSuccess,
      errorMessage: details.errorMessage,
    });
    return response;
  }

  function internalFailure(): LoginFailure {
    return { code: 'server', ...FAILURE_DETAILS.server };
  }

  let readiness: AdminReadinessResult;
  try {
    readiness = dependencies.getReadiness();
  } catch {
    const failure = internalFailure();
    return finish(
      failureResponse(request, mode, destination, failure),
      { errorMessage: failure.message },
    );
  }
  if (!readiness.available) {
    const failure = readinessFailure(readiness.reason);
    return finish(
      failureResponse(request, mode, destination, failure),
      { errorMessage: failure.message },
    );
  }

  let rateLimit: AdminRateLimitResult;
  try {
    rateLimit = dependencies.checkRateLimit(request);
  } catch {
    const failure = internalFailure();
    return finish(
      failureResponse(request, mode, destination, failure),
      { errorMessage: failure.message },
    );
  }
  if (!rateLimit.allowed) {
    const failure =
      rateLimit.reason === 'distributed_limiter_required'
        ? readinessFailure('distributed_limiter_missing')
        : {
            code: 'rate' as const,
            status: 429 as const,
            message: 'Too many login attempts. Try again later.',
            retryAfterSeconds: Math.max(
              1,
              Math.ceil((rateLimit.retryAfterMs ?? 1_000) / 1_000),
            ),
          };
    return finish(
      failureResponse(request, mode, destination, failure),
      { errorMessage: failure.message },
    );
  }

  let password: string;
  try {
    const contentType = request.headers.get('content-type') ?? '';
    if (!contentType.toLowerCase().startsWith('application/x-www-form-urlencoded')) {
      throw new TypeError('Unsupported admin login request body.');
    }
    const formData = await request.formData();
    const passwordValue = formData.get('password');
    if (typeof passwordValue !== 'string') {
      throw new TypeError('Missing admin login password.');
    }
    password = passwordValue;
  } catch {
    const failure: LoginFailure = {
      code: 'invalid_request',
      ...FAILURE_DETAILS.invalid_request,
    };
    return finish(
      failureResponse(request, mode, destination, failure),
      { errorMessage: failure.message },
    );
  }

  let verifiedAuthSuccess: boolean | undefined;
  try {
    const authentication = await dependencies.authenticate(password);
    if (!authentication.ok) {
      verifiedAuthSuccess =
        authentication.reason === 'invalid' ? false : undefined;
      const failure =
        authentication.reason === 'invalid'
          ? ({ code: 'invalid', ...FAILURE_DETAILS.invalid } as LoginFailure)
          : readinessFailure(authentication.reason);
      return finish(
        failureResponse(request, mode, destination, failure),
        {
          authSuccess: verifiedAuthSuccess,
          errorMessage: failure.message,
        },
      );
    }

    verifiedAuthSuccess = true;
    const sessionCookie = await dependencies.createSessionCookie();
    return finish(
      successResponse(request, mode, destination, sessionCookie),
      { authSuccess: true },
    );
  } catch {
    const failure: LoginFailure = {
      code: 'server',
      ...FAILURE_DETAILS.server,
    };
    return finish(
      failureResponse(request, mode, destination, failure),
      { authSuccess: verifiedAuthSuccess, errorMessage: failure.message },
    );
  }
}
