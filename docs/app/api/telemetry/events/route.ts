import { NextResponse } from 'next/server';
import { getRequestId, recordApiObservation } from '@/lib/server/telemetry';
import { recordTelemetryEvent, type TelemetryEventInput } from '@/lib/server/telemetry-store';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type ClientTelemetryPayload = {
  events?: TelemetryEventInput[];
};

type ClientTelemetryEventName = 'page_view' | 'cta_click' | 'outbound_click';

const CLIENT_EVENT_NAMES = new Set<ClientTelemetryEventName>([
  'page_view',
  'cta_click',
  'outbound_click',
]);

function isClientTelemetryEvent(
  event: TelemetryEventInput,
): event is TelemetryEventInput & { name: ClientTelemetryEventName } {
  return CLIENT_EVENT_NAMES.has(event.name as ClientTelemetryEventName);
}

export async function POST(request: Request) {
  const startedAt = performance.now();
  const requestId = getRequestId(request);

  try {
    const body = (await request.json()) as ClientTelemetryPayload;
    const events = Array.isArray(body.events) ? body.events : [];

    const acceptedEvents = events
      .filter(isClientTelemetryEvent)
      .slice(0, 20)
      .map((event) => ({
        ...event,
        source: 'client' as const,
      }));

    await Promise.all(acceptedEvents.map((event) => recordTelemetryEvent(event)));
    await recordApiObservation({
      route: '/api/telemetry/events',
      method: 'POST',
      statusCode: 202,
      durationMs: performance.now() - startedAt,
      requestId,
    });

    return NextResponse.json({ ok: true, accepted: acceptedEvents.length }, { status: 202 });
  } catch (error) {
    await recordApiObservation({
      route: '/api/telemetry/events',
      method: 'POST',
      statusCode: 400,
      durationMs: performance.now() - startedAt,
      requestId,
      errorMessage:
        error instanceof Error ? error.message : 'Invalid telemetry payload.',
    });

    return NextResponse.json(
      { ok: false, error: 'Invalid telemetry payload.' },
      { status: 400 },
    );
  }
}