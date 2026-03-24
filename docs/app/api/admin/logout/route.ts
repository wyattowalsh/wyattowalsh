import { NextResponse } from 'next/server';
import { createClearedAdminSessionCookie } from '@/lib/server/admin-auth';
import { getRequestId, recordApiObservation } from '@/lib/server/telemetry';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const startedAt = performance.now();
  const requestId = getRequestId(request);
  const response = NextResponse.redirect(new URL('/admin/login', request.url), {
    status: 303,
  });
  const clearedCookie = createClearedAdminSessionCookie();
  response.cookies.set(
    clearedCookie.name,
    clearedCookie.value,
    clearedCookie.options,
  );

  await recordApiObservation({
    route: '/api/admin/logout',
    method: 'POST',
    statusCode: 303,
    durationMs: performance.now() - startedAt,
    requestId,
  });

  return response;
}