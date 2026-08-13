import type {
  TelemetryEventInput,
  TelemetryWriteResult,
} from './telemetry-core';

const MAX_CLIENT_EVENTS_PER_REQUEST = 20;
const MAX_CLIENT_TELEMETRY_BODY_BYTES = 32 * 1024;
const MAX_CLIENT_CLOCK_SKEW_MS = 5 * 60 * 1000;
const CLIENT_EVENT_NAMES = new Set([
  'page_view',
  'cta_click',
  'outbound_click',
] as const);

type ClientTelemetryEventName =
  | 'page_view'
  | 'cta_click'
  | 'outbound_click';

type TelemetryIngestionDependencies = {
  recordEvents(
    events: readonly TelemetryEventInput[],
  ): Promise<TelemetryWriteResult>;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function readOptionalString(
  event: Record<string, unknown>,
  field: string,
): string | undefined {
  const value = event[field];
  if (value === undefined) {
    return undefined;
  }
  if (typeof value !== 'string') {
    throw new Error(`Telemetry event field ${field} must be a string.`);
  }
  return value;
}

function parseClientEvent(value: unknown, now: number): TelemetryEventInput {
  if (!isRecord(value)) {
    throw new Error('Telemetry events must be objects.');
  }

  if (
    typeof value.name !== 'string' ||
    !CLIENT_EVENT_NAMES.has(value.name as ClientTelemetryEventName)
  ) {
    throw new Error('Telemetry event name is not accepted from clients.');
  }

  const occurredAt = readOptionalString(value, 'occurredAt');
  if (occurredAt !== undefined) {
    const occurredAtMs = Date.parse(occurredAt);
    if (
      !Number.isFinite(occurredAtMs) ||
      occurredAtMs > now + MAX_CLIENT_CLOCK_SKEW_MS
    ) {
      throw new Error('Telemetry event timestamp is invalid.');
    }
  }

  return {
    name: value.name as ClientTelemetryEventName,
    source: 'client',
    occurredAt,
    sessionId: readOptionalString(value, 'sessionId'),
    pathname: readOptionalString(value, 'pathname'),
    title: readOptionalString(value, 'title'),
    referrer: readOptionalString(value, 'referrer'),
    href: readOptionalString(value, 'href'),
    label: readOptionalString(value, 'label'),
  };
}

export function parseClientTelemetryPayload(
  value: unknown,
  options: { now?: number } = {},
): TelemetryEventInput[] {
  if (!isRecord(value) || !Array.isArray(value.events)) {
    throw new Error('Telemetry payload must contain an events array.');
  }

  if (value.events.length > MAX_CLIENT_EVENTS_PER_REQUEST) {
    throw new Error(
      `Telemetry payload cannot contain more than ${MAX_CLIENT_EVENTS_PER_REQUEST} events.`,
    );
  }

  const now = options.now ?? Date.now();
  return value.events.map((event) => parseClientEvent(event, now));
}

function jsonResponse(body: unknown, status: number): Response {
  return Response.json(body, {
    status,
    headers: { 'Cache-Control': 'no-store' },
  });
}

async function readBoundedRequestBody(request: Request): Promise<string> {
  const contentLength = request.headers.get('content-length');
  if (contentLength !== null) {
    const declaredLength = Number(contentLength);
    if (
      !Number.isSafeInteger(declaredLength) ||
      declaredLength < 0 ||
      declaredLength > MAX_CLIENT_TELEMETRY_BODY_BYTES
    ) {
      throw new Error('Telemetry payload length is invalid.');
    }
  }

  if (!request.body) {
    return '';
  }

  const reader = request.body.getReader();
  const decoder = new TextDecoder();
  let receivedBytes = 0;
  let body = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        return body + decoder.decode();
      }

      receivedBytes += value.byteLength;
      if (receivedBytes > MAX_CLIENT_TELEMETRY_BODY_BYTES) {
        await reader.cancel().catch(() => undefined);
        throw new Error('Telemetry payload is too large.');
      }
      body += decoder.decode(value, { stream: true });
    }
  } finally {
    reader.releaseLock();
  }
}

export async function handlePublicTelemetryIngestion(
  request: Request,
  dependencies: TelemetryIngestionDependencies,
): Promise<Response> {
  let events: TelemetryEventInput[];
  try {
    const body = await readBoundedRequestBody(request);
    events = parseClientTelemetryPayload(JSON.parse(body));
  } catch {
    return jsonResponse(
      { ok: false, error: 'Invalid telemetry payload.' },
      400,
    );
  }

  try {
    const result = await dependencies.recordEvents(events);
    return jsonResponse({ ok: true, ...result }, 202);
  } catch {
    return jsonResponse(
      { ok: false, error: 'Telemetry storage is unavailable.' },
      503,
    );
  }
}
