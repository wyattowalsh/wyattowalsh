import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { describe, it } from 'node:test';

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === 'next/server') {
      return {
        shortCircuit: true,
        url: new URL('../../node_modules/next/server.js', import.meta.url).href,
      };
    }
    if (
      specifier === './admin-destination' &&
      context.parentURL?.endsWith('/admin-login-handler.ts')
    ) {
      return {
        shortCircuit: true,
        url: new URL('./admin-destination.ts', import.meta.url).href,
      };
    }
    return nextResolve(specifier, context);
  },
});

type HandlerModule = typeof import('./admin-login-handler');
const {
  buildAdminLoginAction,
  handleAdminLogin,
  selectAdminLoginResponseMode,
} = (await import(
  new URL('./admin-login-handler.ts', import.meta.url).href
)) as HandlerModule;

type Dependencies = import('./admin-login-handler').AdminLoginDependencies;
type Observation = import('./admin-login-handler').AdminLoginObservation;

function loginRequest(options: {
  accept?: string;
  contentType?: string;
  next?: string;
  password?: string;
  rawBody?: string;
} = {}): Request {
  const url = new URL('https://docs.example/api/admin/login');
  if (options.next !== undefined) {
    url.searchParams.set('next', options.next);
  }
  const body =
    options.rawBody ??
    new URLSearchParams(
      options.password === undefined ? {} : { password: options.password },
    ).toString();
  const headers = new Headers({
    'Content-Type':
      options.contentType ?? 'application/x-www-form-urlencoded;charset=UTF-8',
  });
  if (options.accept !== undefined) {
    headers.set('Accept', options.accept);
  }
  return new Request(url, { method: 'POST', headers, body });
}

function dependencies(
  observations: Observation[],
  overrides: Partial<Dependencies> = {},
): Dependencies {
  return {
    requestId: 'request-1',
    getReadiness: () => ({ available: true }),
    checkRateLimit: () => ({ allowed: true }),
    authenticate: async () => ({ ok: true }),
    createSessionCookie: async () => ({
      name: 'admin_session',
      value: 'session-token',
      options: {
        httpOnly: true,
        sameSite: 'lax',
        secure: true,
        path: '/',
      },
    }),
    recordObservation: async (observation) => {
      observations.push(observation);
    },
    now: () => 100,
    ...overrides,
  };
}

async function responseBody(response: Response): Promise<Record<string, unknown>> {
  return (await response.json()) as Record<string, unknown>;
}

describe('admin login response negotiation', () => {
  it('uses HTML only for an explicit accepted HTML representation', () => {
    assert.equal(selectAdminLoginResponseMode(null), 'json');
    assert.equal(selectAdminLoginResponseMode('*/*'), 'json');
    assert.equal(selectAdminLoginResponseMode('application/json'), 'json');
    assert.equal(selectAdminLoginResponseMode('text/html'), 'html');
    assert.equal(
      selectAdminLoginResponseMode('application/xhtml+xml;q=0.7'),
      'html',
    );
    assert.equal(
      selectAdminLoginResponseMode('text/html, application/json'),
      'html',
    );
    assert.equal(
      selectAdminLoginResponseMode('text/html;q=0.4, application/json;q=0.8'),
      'json',
    );
    assert.equal(
      selectAdminLoginResponseMode('text/html;q=0, application/json;q=0'),
      'json',
    );
    assert.equal(selectAdminLoginResponseMode('text/html;q=broken'), 'json');
  });

  it('builds a query action from a sanitized admin destination', () => {
    const safe = new URL(buildAdminLoginAction('/admin/events?window=30'), 'https://docs.example');
    assert.equal(safe.pathname, '/api/admin/login');
    assert.equal(safe.searchParams.get('next'), '/admin/events?window=30');

    const unsafe = new URL(
      buildAdminLoginAction('//evil.example/admin'),
      'https://docs.example',
    );
    assert.equal(unsafe.searchParams.get('next'), '/admin');
  });
});

describe('admin login handler', () => {
  it('returns negotiated fail-closed readiness responses without authenticating', async () => {
    for (const [accept, expectedStatus] of [
      ['text/html', 303],
      ['application/json', 503],
    ] as const) {
      const observations: Observation[] = [];
      let authenticationCalls = 0;
      const response = await handleAdminLogin(
        loginRequest({ accept, next: '/admin/events?window=7', password: 'pw' }),
        dependencies(observations, {
          getReadiness: () => ({
            available: false,
            reason: 'credentials_missing',
          }),
          authenticate: async () => {
            authenticationCalls += 1;
            return { ok: true };
          },
        }),
      );

      assert.equal(response.status, expectedStatus);
      assert.equal(response.headers.get('cache-control'), 'no-store');
      assert.equal(response.headers.get('vary'), 'Accept');
      assert.equal(authenticationCalls, 0);
      assert.equal(observations.length, 1);
      assert.equal(observations[0]?.statusCode, expectedStatus);
      assert.equal(observations[0]?.authSuccess, undefined);
      if (accept === 'text/html') {
        const location = new URL(response.headers.get('location') ?? '');
        assert.equal(location.origin, 'https://docs.example');
        assert.equal(location.pathname, '/admin/login');
        assert.equal(location.searchParams.get('error'), 'config');
        assert.equal(
          location.searchParams.get('next'),
          '/admin/events?window=7',
        );
      } else {
        assert.deepEqual(await responseBody(response), {
          ok: false,
          code: 'config',
          error: 'Admin credentials are not configured.',
        });
      }
    }
  });

  it('preserves Retry-After while using PRG for HTML and 429 for JSON', async () => {
    for (const [accept, expectedStatus] of [
      ['text/html', 303],
      ['application/json', 429],
    ] as const) {
      const observations: Observation[] = [];
      const response = await handleAdminLogin(
        loginRequest({ accept, password: 'pw' }),
        dependencies(observations, {
          checkRateLimit: () => ({
            allowed: false,
            reason: 'rate_limited',
            retryAfterMs: 1_501,
          }),
        }),
      );
      assert.equal(response.status, expectedStatus);
      assert.equal(response.headers.get('retry-after'), '2');
      assert.equal(observations[0]?.statusCode, expectedStatus);
      assert.equal(observations[0]?.authSuccess, undefined);
      if (accept === 'text/html') {
        const location = new URL(response.headers.get('location') ?? '');
        assert.equal(location.searchParams.get('error'), 'rate');
      } else {
        assert.equal((await responseBody(response)).code, 'rate');
      }
    }
  });

  it('returns bounded invalid-password responses after verification', async () => {
    for (const [accept, expectedStatus] of [
      ['text/html', 303],
      ['application/json', 401],
    ] as const) {
      const observations: Observation[] = [];
      const response = await handleAdminLogin(
        loginRequest({ accept, next: '/admin', password: 'wrong' }),
        dependencies(observations, {
          authenticate: async () => ({ ok: false, reason: 'invalid' }),
        }),
      );
      assert.equal(response.status, expectedStatus);
      assert.equal(observations[0]?.authSuccess, false);
      assert.equal(observations[0]?.statusCode, expectedStatus);
      if (accept === 'text/html') {
        const location = new URL(response.headers.get('location') ?? '');
        assert.equal(location.searchParams.get('error'), 'invalid');
      } else {
        assert.equal((await responseBody(response)).code, 'invalid');
      }
    }
  });

  it('sets the same session cookie for HTML redirects and JSON success', async () => {
    for (const [accept, expectedStatus] of [
      ['text/html', 303],
      ['application/json', 200],
    ] as const) {
      const observations: Observation[] = [];
      const response = await handleAdminLogin(
        loginRequest({
          accept,
          next: '/admin/events?window=30',
          password: 'correct',
        }),
        dependencies(observations),
      );
      assert.equal(response.status, expectedStatus);
      assert.match(response.headers.get('set-cookie') ?? '', /^admin_session=session-token/);
      assert.equal(observations[0]?.authSuccess, true);
      assert.equal(observations[0]?.statusCode, expectedStatus);
      if (accept === 'text/html') {
        assert.equal(
          response.headers.get('location'),
          'https://docs.example/admin/events?window=30',
        );
      } else {
        assert.deepEqual(await responseBody(response), {
          ok: true,
          redirect: '/admin/events?window=30',
        });
      }
    }
  });

  it('rejects malformed bodies before authentication in both representations', async () => {
    for (const [accept, expectedStatus] of [
      ['text/html', 303],
      ['application/json', 400],
    ] as const) {
      const observations: Observation[] = [];
      let authenticationCalls = 0;
      const response = await handleAdminLogin(
        loginRequest({ accept, contentType: 'application/json', rawBody: '{}' }),
        dependencies(observations, {
          authenticate: async () => {
            authenticationCalls += 1;
            return { ok: true };
          },
        }),
      );
      assert.equal(response.status, expectedStatus);
      assert.equal(authenticationCalls, 0);
      assert.equal(observations[0]?.authSuccess, undefined);
      if (accept === 'application/json') {
        assert.equal((await responseBody(response)).code, 'invalid_request');
      }
    }
  });

  it('fails safely on unsafe next paths and rejected telemetry writes', async () => {
    const observations: Observation[] = [];
    const response = await handleAdminLogin(
      loginRequest({
        accept: 'text/html',
        next: '/\\evil.example',
        password: 'correct',
      }),
      dependencies(observations, {
        recordObservation: async (observation) => {
          observations.push(observation);
          throw new Error('telemetry unavailable');
        },
      }),
    );
    assert.equal(response.status, 303);
    assert.equal(response.headers.get('location'), 'https://docs.example/admin');
    assert.match(response.headers.get('set-cookie') ?? '', /^admin_session=session-token/);
    assert.equal(observations[0]?.statusCode, 303);
  });

  it('distinguishes dependency failures from malformed requests', async () => {
    const observations: Observation[] = [];
    const response = await handleAdminLogin(
      loginRequest({ accept: 'application/json', password: 'pw' }),
      dependencies(observations, {
        authenticate: async () => {
          throw new Error('secret backend detail');
        },
      }),
    );
    assert.equal(response.status, 500);
    assert.deepEqual(await responseBody(response), {
      ok: false,
      code: 'server',
      error: 'Admin login operation failed.',
    });
    assert.equal(observations[0]?.authSuccess, undefined);
    assert.equal(observations[0]?.statusCode, 500);
    assert.equal(observations[0]?.errorMessage, 'Admin login operation failed.');
  });

  it('bounds readiness, limiter, and post-auth session dependency failures', async () => {
    for (const [override, expectedAuthSuccess] of [
      [
        {
          getReadiness: () => {
            throw new Error('config detail');
          },
        },
        undefined,
      ],
      [
        {
          checkRateLimit: () => {
            throw new Error('limiter detail');
          },
        },
        undefined,
      ],
      [
        {
          createSessionCookie: async () => {
            throw new Error('session detail');
          },
        },
        true,
      ],
    ] as const) {
      const observations: Observation[] = [];
      const response = await handleAdminLogin(
        loginRequest({ accept: 'application/json', password: 'pw' }),
        dependencies(observations, override),
      );
      assert.equal(response.status, 500);
      assert.equal((await responseBody(response)).code, 'server');
      assert.equal(observations[0]?.statusCode, 500);
      assert.equal(observations[0]?.authSuccess, expectedAuthSuccess);
    }
  });
});
