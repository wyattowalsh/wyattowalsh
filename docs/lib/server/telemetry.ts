import 'server-only';

import { writeTelemetryObservationsBestEffort } from '@/lib/server/public-telemetry-observation';
import {
  recordTelemetryEvents,
  type TelemetryEventInput,
} from '@/lib/server/telemetry-store';

export function getRequestId(request: Request): string {
  return request.headers.get('x-request-id') ?? crypto.randomUUID();
}

export async function recordTelemetryObservations(
  inputs: readonly TelemetryEventInput[],
): Promise<void> {
  await writeTelemetryObservationsBestEffort(recordTelemetryEvents, inputs);
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
  const events: TelemetryEventInput[] = [
    {
      name: 'api_request',
      source: 'server',
      route: input.route,
      method: input.method,
      statusCode: input.statusCode,
      durationMs: input.durationMs,
      requestId: input.requestId,
      sessionId: input.sessionId,
      outcome: input.statusCode >= 400 ? 'error' : 'success',
    },
  ];

  if (input.statusCode >= 400 || input.errorMessage) {
    events.push({
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

  await recordTelemetryObservations(events);
}

export async function recordAdminAuthResult(input: {
  success: boolean;
  requestId: string;
  errorMessage?: string;
}): Promise<void> {
  await recordTelemetryObservations([
    {
      name: input.success ? 'admin_auth_success' : 'admin_auth_failure',
      source: 'server',
      route: '/admin/login',
      method: 'POST',
      requestId: input.requestId,
      outcome: input.success ? 'success' : 'denied',
      errorMessage: input.errorMessage,
    },
  ]);
}
