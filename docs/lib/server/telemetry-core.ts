export type TelemetryBackend = 'disabled' | 'filesystem' | 'redis';

export type TelemetryAvailability =
  | 'available'
  | 'disabled'
  | 'unavailable';

export type TelemetryEventName =
  | 'page_view'
  | 'cta_click'
  | 'outbound_click'
  | 'docs_search'
  | 'admin_auth_success'
  | 'admin_auth_failure'
  | 'api_request'
  | 'api_error';

export type TelemetryEventSource = 'client' | 'server';

export type TelemetryEvent = {
  id: string;
  name: TelemetryEventName;
  source: TelemetryEventSource;
  occurredAt: string;
  sessionId?: string;
  pathname?: string;
  title?: string;
  referrer?: string;
  href?: string;
  label?: string;
  searchQuery?: string;
  route?: string;
  method?: string;
  statusCode?: number;
  durationMs?: number;
  outcome?: 'success' | 'error' | 'denied';
  requestId?: string;
  errorMessage?: string;
  metadata?: Record<string, string | number | boolean>;
};

export type TelemetryEventInput = Omit<TelemetryEvent, 'id' | 'occurredAt'> & {
  occurredAt?: string;
};

export type TelemetryStoreData = {
  version: 1;
  events: TelemetryEvent[];
};

export type TelemetryWriteResult = {
  mode: TelemetryBackend;
  received: number;
  stored: number;
};

export type TelemetryDashboardSnapshot = {
  adapter: TelemetryBackend;
  availability: TelemetryAvailability;
  unavailableReason?: 'disabled' | 'configuration' | 'backend';
  /** Deliberately redacted; never contains a Redis URL/token or absolute path. */
  storageTarget: string;
  totalRetainedEvents: number;
  windowDays: number;
  summary: {
    pageViews: number;
    uniqueSessions: number;
    searches: number;
    ctaClicks: number;
    outboundClicks: number;
    authFailures: number;
    apiRequests: number;
    apiErrors: number;
    averageApiLatencyMs: number;
  };
  timeline: Array<{
    label: string;
    pageViews: number;
    searches: number;
    ctaClicks: number;
    apiErrors: number;
  }>;
  topPages: Array<{ pathname: string; title?: string; views: number }>;
  topReferrers: Array<{ referrer: string; visits: number }>;
  topSearches: Array<{ query: string; count: number }>;
  topCallsToAction: Array<{ label: string; count: number }>;
  routeHealth: Array<{
    route: string;
    requests: number;
    errors: number;
    averageLatencyMs: number;
    maxLatencyMs: number;
    lastStatusCode?: number;
  }>;
  recentEvents: TelemetryEvent[];
};

export type TelemetrySnapshotMetadata = Pick<
  TelemetryDashboardSnapshot,
  'adapter' | 'availability' | 'unavailableReason' | 'storageTarget'
>;

const EVENT_NAMES = new Set<TelemetryEventName>([
  'page_view',
  'cta_click',
  'outbound_click',
  'docs_search',
  'admin_auth_success',
  'admin_auth_failure',
  'api_request',
  'api_error',
]);

const EVENT_SOURCES = new Set<TelemetryEventSource>(['client', 'server']);
const EVENT_OUTCOMES = new Set(['success', 'error', 'denied']);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isOptionalString(value: unknown): value is string | undefined {
  return value === undefined || typeof value === 'string';
}

function isOptionalFiniteNumber(
  value: unknown,
): value is number | undefined {
  return value === undefined || (typeof value === 'number' && Number.isFinite(value));
}

function isTelemetryMetadata(
  value: unknown,
): value is Record<string, string | number | boolean> | undefined {
  return (
    value === undefined ||
    (isRecord(value) &&
      Object.values(value).every(
        (item) =>
          typeof item === 'string' ||
          typeof item === 'number' ||
          typeof item === 'boolean',
      ))
  );
}

export function isTelemetryEvent(value: unknown): value is TelemetryEvent {
  if (!isRecord(value)) {
    return false;
  }

  if (
    typeof value.id !== 'string' ||
    value.id.length === 0 ||
    typeof value.name !== 'string' ||
    !EVENT_NAMES.has(value.name as TelemetryEventName) ||
    typeof value.source !== 'string' ||
    !EVENT_SOURCES.has(value.source as TelemetryEventSource) ||
    typeof value.occurredAt !== 'string' ||
    !Number.isFinite(Date.parse(value.occurredAt))
  ) {
    return false;
  }

  return (
    isOptionalString(value.sessionId) &&
    isOptionalString(value.pathname) &&
    isOptionalString(value.title) &&
    isOptionalString(value.referrer) &&
    isOptionalString(value.href) &&
    isOptionalString(value.label) &&
    isOptionalString(value.searchQuery) &&
    isOptionalString(value.route) &&
    isOptionalString(value.method) &&
    isOptionalFiniteNumber(value.statusCode) &&
    isOptionalFiniteNumber(value.durationMs) &&
    (value.outcome === undefined || EVENT_OUTCOMES.has(String(value.outcome))) &&
    isOptionalString(value.requestId) &&
    isOptionalString(value.errorMessage) &&
    isTelemetryMetadata(value.metadata)
  );
}

export function parseTelemetryStoreData(value: unknown): TelemetryStoreData {
  if (
    !isRecord(value) ||
    value.version !== 1 ||
    !Array.isArray(value.events) ||
    !value.events.every(isTelemetryEvent)
  ) {
    throw new Error('Telemetry store data is invalid.');
  }

  return {
    version: 1,
    events: value.events.map(sanitizePersistedTelemetryEvent),
  };
}

function sanitizeScalar(value: unknown, maxLength = 240): string | undefined {
  if (typeof value !== 'string') {
    return undefined;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed.slice(0, maxLength) : undefined;
}

function sanitizePathname(value: unknown): string | undefined {
  const trimmed = sanitizeScalar(value, 240);
  if (!trimmed?.startsWith('/') || trimmed.startsWith('//')) {
    return undefined;
  }
  return trimmed.split(/[?#]/, 1)[0]?.slice(0, 240);
}

function sanitizeReferrer(value: unknown): string | undefined {
  const trimmed = sanitizeScalar(value, 320);
  if (!trimmed) {
    return undefined;
  }

  try {
    const url = new URL(trimmed);
    return `${url.origin}${url.pathname}`.slice(0, 320);
  } catch {
    return undefined;
  }
}

function sanitizeHref(value: unknown): string | undefined {
  const trimmed = sanitizeScalar(value, 320);
  if (!trimmed) {
    return undefined;
  }

  try {
    const url = new URL(trimmed);
    return `${url.origin}${url.pathname}`.slice(0, 320);
  } catch {
    return sanitizePathname(trimmed);
  }
}

function sanitizeMetadata(
  value: TelemetryEventInput['metadata'],
): Record<string, string | number | boolean> | undefined {
  if (!isRecord(value)) {
    return undefined;
  }

  const entries = Object.entries(value)
    .slice(0, 20)
    .flatMap(([key, item]) => {
      const normalizedKey = sanitizeScalar(key, 48);
      if (!normalizedKey) {
        return [];
      }

      if (
        typeof item === 'string' ||
        typeof item === 'number' ||
        typeof item === 'boolean'
      ) {
        if (typeof item === 'number' && !Number.isFinite(item)) {
          return [];
        }
        return [
          [normalizedKey, typeof item === 'string' ? item.slice(0, 160) : item],
        ] as Array<[string, string | number | boolean]>;
      }

      return [];
    });

  return entries.length > 0 ? Object.fromEntries(entries) : undefined;
}

function sanitizePersistedTelemetryEvent(event: TelemetryEvent): TelemetryEvent {
  const statusCode =
    typeof event.statusCode === 'number' &&
    Number.isInteger(event.statusCode) &&
    event.statusCode >= 100 &&
    event.statusCode <= 599
      ? event.statusCode
      : undefined;

  return {
    id: event.id.slice(0, 80),
    name: event.name,
    source: event.source,
    occurredAt: new Date(Date.parse(event.occurredAt)).toISOString(),
    sessionId: sanitizeScalar(event.sessionId, 80),
    pathname: sanitizePathname(event.pathname),
    title: sanitizeScalar(event.title, 120),
    referrer: sanitizeReferrer(event.referrer),
    href: sanitizeHref(event.href),
    label: sanitizeScalar(event.label, 120),
    searchQuery: sanitizeScalar(event.searchQuery, 120),
    route: sanitizePathname(event.route),
    method: sanitizeScalar(event.method, 12)?.toUpperCase(),
    statusCode,
    durationMs:
      typeof event.durationMs === 'number' && Number.isFinite(event.durationMs)
        ? Math.max(0, Math.round(event.durationMs))
        : undefined,
    outcome:
      event.outcome !== undefined && EVENT_OUTCOMES.has(event.outcome)
        ? event.outcome
        : undefined,
    requestId: sanitizeScalar(event.requestId, 80),
    errorMessage: sanitizeScalar(event.errorMessage, 240),
    metadata: sanitizeMetadata(event.metadata),
  };
}

export function normalizeTelemetryEvent(
  input: TelemetryEventInput,
  options: { now?: number; createId?: () => string } = {},
): TelemetryEvent {
  if (!EVENT_NAMES.has(input.name) || !EVENT_SOURCES.has(input.source)) {
    throw new Error('Telemetry event name or source is invalid.');
  }
  if (input.outcome !== undefined && !EVENT_OUTCOMES.has(input.outcome)) {
    throw new Error('Telemetry event outcome is invalid.');
  }

  const now = options.now ?? Date.now();
  const occurredAt = input.occurredAt ?? new Date(now).toISOString();
  const occurredAtMs = Date.parse(occurredAt);
  if (!Number.isFinite(occurredAtMs)) {
    throw new Error('Telemetry event timestamp is invalid.');
  }
  if (occurredAtMs > now + 5 * 60 * 1000) {
    throw new Error('Telemetry event timestamp is in the future.');
  }

  const statusCode =
    typeof input.statusCode === 'number' &&
    Number.isInteger(input.statusCode) &&
    input.statusCode >= 100 &&
    input.statusCode <= 599
      ? input.statusCode
      : undefined;

  return {
    id: options.createId?.() ?? crypto.randomUUID(),
    name: input.name,
    source: input.source,
    occurredAt,
    sessionId: sanitizeScalar(input.sessionId, 80),
    pathname: sanitizePathname(input.pathname),
    title: sanitizeScalar(input.title, 120),
    referrer: sanitizeReferrer(input.referrer),
    href: sanitizeHref(input.href),
    label: sanitizeScalar(input.label, 120),
    searchQuery: sanitizeScalar(input.searchQuery, 120),
    route: sanitizePathname(input.route),
    method: sanitizeScalar(input.method, 12)?.toUpperCase(),
    statusCode,
    durationMs:
      typeof input.durationMs === 'number' && Number.isFinite(input.durationMs)
        ? Math.max(0, Math.round(input.durationMs))
        : undefined,
    outcome: input.outcome,
    requestId: sanitizeScalar(input.requestId, 80),
    errorMessage: sanitizeScalar(input.errorMessage, 240),
    metadata: sanitizeMetadata(input.metadata),
  };
}

export function appendRetainedTelemetryEvents(input: {
  existing: readonly TelemetryEvent[];
  additions: readonly TelemetryEvent[];
  now: number;
  retentionDays: number;
  maxEvents: number;
}): TelemetryEvent[] {
  const retentionThreshold =
    input.now - input.retentionDays * 24 * 60 * 60 * 1000;
  const retainedEvents = [...input.existing, ...input.additions].filter((event) => {
    const timestamp = Date.parse(event.occurredAt);
    return (
      Number.isFinite(timestamp) &&
      timestamp >= retentionThreshold &&
      timestamp <= input.now + 5 * 60 * 1000
    );
  });
  if (retainedEvents.length > input.maxEvents) {
    retainedEvents.splice(0, retainedEvents.length - input.maxEvents);
  }
  return retainedEvents;
}

function bucketLabel(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function buildTelemetryDashboardSnapshot(input: {
  events: readonly TelemetryEvent[];
  windowDays: number;
  metadata: TelemetrySnapshotMetadata;
  now?: number;
}): TelemetryDashboardSnapshot {
  const now = input.now ?? Date.now();
  const threshold = now - input.windowDays * 24 * 60 * 60 * 1000;
  const events = input.events.filter((event) => {
    const timestamp = Date.parse(event.occurredAt);
    return timestamp >= threshold && timestamp <= now + 5 * 60 * 1000;
  });

  const pageCounts = new Map<
    string,
    { pathname: string; title?: string; views: number }
  >();
  const referrerCounts = new Map<string, number>();
  const searchCounts = new Map<string, number>();
  const ctaCounts = new Map<string, number>();
  const routeHealth = new Map<
    string,
    {
      route: string;
      requests: number;
      errors: number;
      latencyTotal: number;
      maxLatencyMs: number;
      lastStatusCode?: number;
    }
  >();
  const timeline = new Map<
    string,
    {
      label: string;
      pageViews: number;
      searches: number;
      ctaClicks: number;
      apiErrors: number;
    }
  >();
  const uniqueSessions = new Set<string>();

  let pageViews = 0;
  let searches = 0;
  let ctaClicks = 0;
  let outboundClicks = 0;
  let authFailures = 0;
  let apiRequests = 0;
  let apiErrors = 0;
  let apiLatencyTotal = 0;

  for (const event of events) {
    if (event.sessionId) {
      uniqueSessions.add(event.sessionId);
    }

    const label = bucketLabel(new Date(event.occurredAt));
    const timelineBucket = timeline.get(label) ?? {
      label,
      pageViews: 0,
      searches: 0,
      ctaClicks: 0,
      apiErrors: 0,
    };

    if (event.name === 'page_view' && event.pathname) {
      pageViews += 1;
      timelineBucket.pageViews += 1;
      const current = pageCounts.get(event.pathname) ?? {
        pathname: event.pathname,
        title: event.title,
        views: 0,
      };
      current.views += 1;
      current.title = current.title ?? event.title;
      pageCounts.set(event.pathname, current);
      if (event.referrer) {
        referrerCounts.set(
          event.referrer,
          (referrerCounts.get(event.referrer) ?? 0) + 1,
        );
      }
    }

    if (event.name === 'docs_search' && event.searchQuery) {
      searches += 1;
      timelineBucket.searches += 1;
      searchCounts.set(
        event.searchQuery,
        (searchCounts.get(event.searchQuery) ?? 0) + 1,
      );
    }

    if (event.name === 'cta_click' && event.label) {
      ctaClicks += 1;
      timelineBucket.ctaClicks += 1;
      ctaCounts.set(event.label, (ctaCounts.get(event.label) ?? 0) + 1);
    }

    if (event.name === 'outbound_click') {
      outboundClicks += 1;
    }

    if (event.name === 'admin_auth_failure') {
      authFailures += 1;
    }

    if (event.name === 'api_request') {
      apiRequests += 1;
      apiLatencyTotal += event.durationMs ?? 0;
      const key = event.route ?? 'unknown';
      const current = routeHealth.get(key) ?? {
        route: key,
        requests: 0,
        errors: 0,
        latencyTotal: 0,
        maxLatencyMs: 0,
        lastStatusCode: undefined,
      };
      current.requests += 1;
      current.latencyTotal += event.durationMs ?? 0;
      current.maxLatencyMs = Math.max(
        current.maxLatencyMs,
        event.durationMs ?? 0,
      );
      current.lastStatusCode = event.statusCode ?? current.lastStatusCode;
      routeHealth.set(key, current);
    }

    if (event.name === 'api_error') {
      apiErrors += 1;
      timelineBucket.apiErrors += 1;
      const key = event.route ?? 'unknown';
      const current = routeHealth.get(key) ?? {
        route: key,
        requests: 0,
        errors: 0,
        latencyTotal: 0,
        maxLatencyMs: 0,
        lastStatusCode: undefined,
      };
      current.errors += 1;
      current.lastStatusCode = event.statusCode ?? current.lastStatusCode;
      routeHealth.set(key, current);
    }

    timeline.set(label, timelineBucket);
  }

  return {
    ...input.metadata,
    totalRetainedEvents: input.events.length,
    windowDays: input.windowDays,
    summary: {
      pageViews,
      uniqueSessions: uniqueSessions.size,
      searches,
      ctaClicks,
      outboundClicks,
      authFailures,
      apiRequests,
      apiErrors,
      averageApiLatencyMs:
        apiRequests > 0 ? Math.round(apiLatencyTotal / apiRequests) : 0,
    },
    timeline: Array.from(timeline.values()).sort((left, right) =>
      left.label.localeCompare(right.label),
    ),
    topPages: Array.from(pageCounts.values())
      .sort((left, right) => right.views - left.views)
      .slice(0, 8),
    topReferrers: Array.from(referrerCounts.entries())
      .map(([referrer, visits]) => ({ referrer, visits }))
      .sort((left, right) => right.visits - left.visits)
      .slice(0, 8),
    topSearches: Array.from(searchCounts.entries())
      .map(([query, count]) => ({ query, count }))
      .sort((left, right) => right.count - left.count)
      .slice(0, 8),
    topCallsToAction: Array.from(ctaCounts.entries())
      .map(([label, count]) => ({ label, count }))
      .sort((left, right) => right.count - left.count)
      .slice(0, 8),
    routeHealth: Array.from(routeHealth.values())
      .map((route) => ({
        route: route.route,
        requests: route.requests,
        errors: route.errors,
        averageLatencyMs:
          route.requests > 0
            ? Math.round(route.latencyTotal / route.requests)
            : 0,
        maxLatencyMs: route.maxLatencyMs,
        lastStatusCode: route.lastStatusCode,
      }))
      .sort((left, right) => right.requests - left.requests)
      .slice(0, 8),
    recentEvents: [...events]
      .sort((left, right) => right.occurredAt.localeCompare(left.occurredAt))
      .slice(0, 20),
  };
}
