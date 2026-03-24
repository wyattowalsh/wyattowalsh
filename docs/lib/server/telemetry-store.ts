import 'server-only';

import { Redis } from '@upstash/redis';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import {
  getDocsServerConfig,
  isPersistentTelemetryConfigured,
} from '@/lib/server/config';

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

type TelemetryStoreData = {
  version: 1;
  events: TelemetryEvent[];
};

export type TelemetryDashboardSnapshot = {
  adapter: 'filesystem' | 'upstash-redis';
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

const EMPTY_STORE: TelemetryStoreData = {
  version: 1,
  events: [],
};

let writeQueue: Promise<void> = Promise.resolve();
let redisClient: Redis | null | undefined;

type ResolvedStore = {
  adapter: 'filesystem' | 'upstash-redis';
  storageTarget: string;
  data: TelemetryStoreData;
};

function resolveStorePath(): string {
  return path.resolve(process.cwd(), getDocsServerConfig().telemetryStorePath);
}

function getRedisClient(): Redis | null {
  if (redisClient !== undefined) {
    return redisClient;
  }

  const config = getDocsServerConfig();
  if (!isPersistentTelemetryConfigured(config)) {
    redisClient = null;
    return redisClient;
  }

  redisClient = new Redis({
    url: config.telemetryRedisRestUrl!,
    token: config.telemetryRedisRestToken!,
  });

  return redisClient;
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
  return trimmed?.startsWith('/') ? trimmed : undefined;
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
    return trimmed;
  }
}

function sanitizeMetadata(
  value: TelemetryEventInput['metadata'],
): Record<string, string | number | boolean> | undefined {
  if (!value) {
    return undefined;
  }

  const entries = Object.entries(value)
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
        return [
          [normalizedKey, typeof item === 'string' ? item.slice(0, 160) : item],
        ] as Array<[string, string | number | boolean]>;
      }

      return [];
    });

  return entries.length > 0 ? Object.fromEntries(entries) : undefined;
}

function normalizeEvent(input: TelemetryEventInput): TelemetryEvent {
  return {
    id: crypto.randomUUID(),
    name: input.name,
    source: input.source,
    occurredAt: input.occurredAt ?? new Date().toISOString(),
    sessionId: sanitizeScalar(input.sessionId, 80),
    pathname: sanitizePathname(input.pathname),
    title: sanitizeScalar(input.title, 120),
    referrer: sanitizeReferrer(input.referrer),
    href: sanitizeScalar(input.href, 320),
    label: sanitizeScalar(input.label, 120),
    searchQuery: sanitizeScalar(input.searchQuery, 120),
    route: sanitizePathname(input.route),
    method: sanitizeScalar(input.method, 12)?.toUpperCase(),
    statusCode:
      typeof input.statusCode === 'number' && Number.isFinite(input.statusCode)
        ? input.statusCode
        : undefined,
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

async function ensureStoreDirectory(): Promise<string> {
  const storePath = resolveStorePath();
  await mkdir(path.dirname(storePath), { recursive: true });
  return storePath;
}

async function readFilesystemStore(): Promise<TelemetryStoreData> {
  const storePath = await ensureStoreDirectory();

  try {
    const content = await readFile(storePath, 'utf8');
    const parsed = JSON.parse(content) as Partial<TelemetryStoreData>;
    if (!Array.isArray(parsed.events)) {
      return EMPTY_STORE;
    }

    return {
      version: 1,
      events: parsed.events,
    };
  } catch {
    return EMPTY_STORE;
  }
}

async function writeFilesystemStore(data: TelemetryStoreData): Promise<void> {
  const storePath = await ensureStoreDirectory();
  await writeFile(storePath, JSON.stringify(data, null, 2), 'utf8');
}

async function readRedisStore(): Promise<TelemetryStoreData> {
  const redis = getRedisClient();
  const config = getDocsServerConfig();
  if (!redis) {
    return EMPTY_STORE;
  }

  const content = await redis.get<string>(config.telemetryRedisKey);
  if (!content) {
    return EMPTY_STORE;
  }

  try {
    const parsed = JSON.parse(content) as Partial<TelemetryStoreData>;
    if (!Array.isArray(parsed.events)) {
      return EMPTY_STORE;
    }

    return {
      version: 1,
      events: parsed.events,
    };
  } catch {
    return EMPTY_STORE;
  }
}

async function writeRedisStore(data: TelemetryStoreData): Promise<void> {
  const redis = getRedisClient();
  const config = getDocsServerConfig();
  if (!redis) {
    return;
  }

  await redis.set(config.telemetryRedisKey, JSON.stringify(data));
}

async function readStore(): Promise<ResolvedStore> {
  const config = getDocsServerConfig();

  if (isPersistentTelemetryConfigured(config)) {
    try {
      return {
        adapter: 'upstash-redis',
        storageTarget: config.telemetryRedisKey,
        data: await readRedisStore(),
      };
    } catch {
      // Fall back to filesystem if Redis is configured but currently unreachable.
    }
  }

  return {
    adapter: 'filesystem',
    storageTarget: resolveStorePath(),
    data: await readFilesystemStore(),
  };
}

async function writeStore(data: TelemetryStoreData): Promise<void> {
  const config = getDocsServerConfig();

  if (isPersistentTelemetryConfigured(config)) {
    try {
      await writeRedisStore(data);
      return;
    } catch {
      // Fall back to filesystem if Redis is configured but currently unreachable.
    }
  }

  await writeFilesystemStore(data);
}

export async function recordTelemetryEvent(
  input: TelemetryEventInput,
): Promise<void> {
  const config = getDocsServerConfig();
  const normalizedEvent = normalizeEvent(input);

  writeQueue = writeQueue.then(async () => {
    const store = await readStore();
    const retentionThreshold =
      Date.now() - config.telemetryRetentionDays * 24 * 60 * 60 * 1000;
    const retainedEvents = store.data.events.filter((event) => {
      const timestamp = Date.parse(event.occurredAt);
      return Number.isFinite(timestamp) && timestamp >= retentionThreshold;
    });

    retainedEvents.push(normalizedEvent);

    if (retainedEvents.length > config.telemetryMaxEvents) {
      retainedEvents.splice(0, retainedEvents.length - config.telemetryMaxEvents);
    }

    await writeStore({
      version: 1,
      events: retainedEvents,
    });
  });

  await writeQueue;
}

function bucketLabel(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export async function getTelemetryDashboardSnapshot(
  windowDays: number,
): Promise<TelemetryDashboardSnapshot> {
  const store = await readStore();
  const now = Date.now();
  const threshold = now - windowDays * 24 * 60 * 60 * 1000;
  const events = store.data.events.filter(
    (event) => Date.parse(event.occurredAt) >= threshold,
  );

  const pageCounts = new Map<string, { pathname: string; title?: string; views: number }>();
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
    { label: string; pageViews: number; searches: number; ctaClicks: number; apiErrors: number }
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

    const date = new Date(event.occurredAt);
    const label = bucketLabel(date);
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
      current.maxLatencyMs = Math.max(current.maxLatencyMs, event.durationMs ?? 0);
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
    adapter: store.adapter,
    storageTarget: store.storageTarget,
    totalRetainedEvents: store.data.events.length,
    windowDays,
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
          route.requests > 0 ? Math.round(route.latencyTotal / route.requests) : 0,
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