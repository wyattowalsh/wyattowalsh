import 'server-only';

import { recordTelemetryEvent } from '@/lib/server/telemetry-store';

export function getRequestId(request: Request): string {
  return request.headers.get('x-request-id') ?? crypto.randomUUID();
}

export async function recordApiObservation(input: {
  route: string;
  method: string;
  statusCode: number;
  durationMs: number;
  requestId: string;
  errorMessage?: string;
  sessionId?: string;
}): Promise<void> {
  await recordTelemetryEvent({
    name: 'api_request',
    source: 'server',
    route: input.route,
    method: input.method,
    statusCode: input.statusCode,
    durationMs: input.durationMs,
    requestId: input.requestId,
    sessionId: input.sessionId,
    outcome: input.statusCode >= 500 ? 'error' : 'success',
  });

  if (input.statusCode >= 400 || input.errorMessage) {
    await recordTelemetryEvent({
      name: 'api_error',
      source: 'server',
      route: input.route,
      method: input.method,
      statusCode: input.statusCode,
      durationMs: input.durationMs,
      requestId: input.requestId,
      sessionId: input.sessionId,
      errorMessage: input.errorMessage,
      outcome: 'error',
    });
  }
}

export async function recordAdminAuthResult(input: {
  success: boolean;
  requestId: string;
  errorMessage?: string;
}): Promise<void> {
  await recordTelemetryEvent({
    name: input.success ? 'admin_auth_success' : 'admin_auth_failure',
    source: 'server',
    route: '/admin/login',
    method: 'POST',
    requestId: input.requestId,
    outcome: input.success ? 'success' : 'denied',
    errorMessage: input.errorMessage,
  });
}