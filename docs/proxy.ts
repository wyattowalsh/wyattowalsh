import { NextResponse, type NextRequest } from 'next/server';
import { parseAdminDestination } from '@/lib/server/admin-destination';
import { getAdminReadiness, getDocsServerConfig } from '@/lib/server/config';
import { ADMIN_SESSION_COOKIE, verifyAdminSessionToken } from '@/lib/server/session';

function isPublicAdminPath(pathname: string): boolean {
  return pathname === '/admin/login' || pathname === '/api/admin/login';
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (isPublicAdminPath(pathname) || pathname === '/api/admin/logout') {
    return NextResponse.next();
  }

  const config = getDocsServerConfig();
  const readiness = getAdminReadiness(config);
  if (!readiness.available) {
    const credentialsMissing = readiness.reason === 'credentials_missing';
    const errorCode = credentialsMissing ? 'config' : 'limiter';
    const errorMessage = credentialsMissing
      ? 'Admin access is not configured.'
      : 'A production-safe distributed login limiter is unavailable.';
    if (pathname.startsWith('/api/admin/')) {
      return NextResponse.json(
        { ok: false, code: errorCode, error: errorMessage },
        { status: 503 },
      );
    }

    const loginUrl = new URL('/admin/login', request.url);
    loginUrl.searchParams.set('error', errorCode);
    return NextResponse.redirect(loginUrl);
  }

  const token = request.cookies.get(ADMIN_SESSION_COOKIE)?.value;
  const session = token
    ? await verifyAdminSessionToken(token, config.sessionSecret)
    : null;

  if (session) {
    return NextResponse.next();
  }

  if (pathname.startsWith('/api/admin/')) {
    return NextResponse.json(
      { ok: false, error: 'Authentication required.' },
      { status: 401 },
    );
  }

  const loginUrl = new URL('/admin/login', request.url);
  loginUrl.searchParams.set(
    'next',
    parseAdminDestination(`${pathname}${request.nextUrl.search}`),
  );
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ['/admin/:path*', '/api/admin/:path*'],
};
