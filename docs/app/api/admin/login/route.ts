import { NextResponse } from 'next/server';
import {
  authenticateAdminPassword,
  createAdminSessionCookie,
} from '@/lib/server/admin-auth';
import { recordAdminAuthResult, recordApiObservation, getRequestId } from '@/lib/server/telemetry';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const loginAttempts = new Map<string, number[]>();
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 5;

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const attempts = loginAttempts.get(ip) ?? [];
  const recent = attempts.filter((t) => now - t < RATE_LIMIT_WINDOW_MS);
  if (recent.length >= RATE_LIMIT_MAX) {
    loginAttempts.set(ip, recent);
    return true;
  }
  recent.push(now);
  loginAttempts.set(ip, recent);
  return false;
}

export async function POST(request: Request) {
  const startedAt = performance.now();
  const requestId = getRequestId(request);

  const ip = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ?? 'unknown';
  if (isRateLimited(ip)) {
    return NextResponse.json(
      { error: 'Too many login attempts. Try again later.' },
      { status: 429 },
    );
  }

  try {
    const formData = await request.formData();
    const password = String(formData.get('password') ?? '');
    const nextPath = String(formData.get('next') ?? '/admin');
    const destination = nextPath.startsWith('/') && !nextPath.startsWith('//') ? nextPath : '/admin';

    const authentication = await authenticateAdminPassword(password);
    if (!authentication.ok) {
      await recordAdminAuthResult({
        success: false,
        requestId,
        errorMessage:
          authentication.reason === 'misconfigured'
            ? 'Admin credentials are not configured.'
            : 'Invalid admin password.',
      });

      const response = NextResponse.redirect(
        new URL(
          authentication.reason === 'misconfigured'
            ? '/admin/login?error=config'
            : '/admin/login?error=invalid',
          request.url,
        ),
        { status: 303 },
      );

      await recordApiObservation({
        route: '/api/admin/login',
        method: 'POST',
        statusCode: 303,
        durationMs: performance.now() - startedAt,
        requestId,
        errorMessage:
          authentication.reason === 'misconfigured'
            ? 'Admin credentials are not configured.'
            : 'Invalid admin password.',
      });
      return response;
    }

    const sessionCookie = await createAdminSessionCookie();
    const response = NextResponse.redirect(new URL(destination, request.url), {
      status: 303,
    });
    response.cookies.set(
      sessionCookie.name,
      sessionCookie.value,
      sessionCookie.options,
    );

    await Promise.all([
      recordAdminAuthResult({ success: true, requestId }),
      recordApiObservation({
        route: '/api/admin/login',
        method: 'POST',
        statusCode: 303,
        durationMs: performance.now() - startedAt,
        requestId,
      }),
    ]);

    return response;
  } catch (error) {
    await Promise.all([
      recordAdminAuthResult({
        success: false,
        requestId,
        errorMessage: 'Unexpected login failure.',
      }),
      recordApiObservation({
        route: '/api/admin/login',
        method: 'POST',
        statusCode: 500,
        durationMs: performance.now() - startedAt,
        requestId,
        errorMessage:
          error instanceof Error ? error.message : 'Unknown login error.',
      }),
    ]);

    return NextResponse.redirect(new URL('/admin/login?error=server', request.url), {
      status: 303,
    });
  }
}