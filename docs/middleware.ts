import { NextResponse, type NextRequest } from 'next/server';
import { getDocsServerConfig, isAdminConfigured } from '@/lib/server/config';
import { ADMIN_SESSION_COOKIE, verifyAdminSessionToken } from '@/lib/server/session';

function isPublicAdminPath(pathname: string): boolean {
  return pathname === '/admin/login' || pathname === '/api/admin/login';
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (isPublicAdminPath(pathname) || pathname === '/api/admin/logout') {
    return NextResponse.next();
  }

  const config = getDocsServerConfig();
  if (!isAdminConfigured(config)) {
    if (pathname.startsWith('/api/admin/')) {
      return NextResponse.json(
        { ok: false, error: 'Admin access is not configured.' },
        { status: 503 },
      );
    }

    return NextResponse.redirect(new URL('/admin/login?error=config', request.url));
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
  loginUrl.searchParams.set('next', pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ['/admin/:path*', '/api/admin/:path*'],
};