import {
  authenticateAdminPassword,
  createAdminSessionCookie,
} from '@/lib/server/admin-auth';
import {
  handleAdminLogin,
  type AdminLoginObservation,
} from '@/lib/server/admin-login-handler';
import {
  createMemoryAdminLoginRateLimiter,
  evaluateAdminLoginRateLimit,
  normalizeAdminLoginClientKey,
} from '@/lib/server/admin-rate-limit';
import {
  getAdminReadiness,
  getDocsServerConfig,
} from '@/lib/server/config';
import {
  getRequestId,
  recordAdminAuthResult,
  recordApiObservation,
} from '@/lib/server/telemetry';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const developmentLoginRateLimiter = createMemoryAdminLoginRateLimiter();

async function recordLoginObservation(
  observation: AdminLoginObservation,
): Promise<void> {
  const records: Promise<void>[] = [
    recordApiObservation({
      route: '/api/admin/login',
      method: 'POST',
      statusCode: observation.statusCode,
      durationMs: performance.now() - observation.startedAt,
      requestId: observation.requestId,
      errorMessage: observation.errorMessage,
    }),
  ];
  if (observation.authSuccess !== undefined) {
    records.push(
      recordAdminAuthResult({
        success: observation.authSuccess,
        requestId: observation.requestId,
        errorMessage: observation.errorMessage,
      }),
    );
  }

  // Observability must never change the result of an authentication attempt.
  await Promise.allSettled(records);
}

export async function POST(request: Request) {
  const config = getDocsServerConfig();
  return handleAdminLogin(request, {
    requestId: getRequestId(request),
    getReadiness: () => getAdminReadiness(config),
    checkRateLimit: (loginRequest) =>
      evaluateAdminLoginRateLimit({
        clientKey: normalizeAdminLoginClientKey(
          loginRequest.headers.get('x-forwarded-for') ??
            loginRequest.headers.get('x-real-ip'),
        ),
        isProduction: config.isProduction,
        limiter: developmentLoginRateLimiter,
      }),
    authenticate: authenticateAdminPassword,
    createSessionCookie: createAdminSessionCookie,
    recordObservation: recordLoginObservation,
  });
}
