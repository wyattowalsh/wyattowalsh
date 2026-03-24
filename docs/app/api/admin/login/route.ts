import { NextResponse } from 'next/server';
import {
  authenticateAdminPassword,
  createAdminSessionCookie,
} from '@/lib/server/admin-auth';
import { recordAdminAuthResult, recordApiObservation, getRequestId } from '@/lib/server/telemetry';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const startedAt = performance.now();
  const requestId = getRequestId(request);

  try {
    const formData = await request.formData();
    const password = String(formData.get('password') ?? '');
    const nextPath = String(formData.get('next') ?? '/admin');
    const destination = nextPath.startsWith('/') ? nextPath : '/admin';

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