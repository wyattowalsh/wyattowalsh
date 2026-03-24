export type DocsServerConfig = {
  adminPassword: string;
  sessionSecret: string;
  telemetryStorePath: string;
  telemetryRetentionDays: number;
  telemetryMaxEvents: number;
  telemetryRedisRestUrl?: string;
  telemetryRedisRestToken?: string;
  telemetryRedisKey: string;
  isProduction: boolean;
};

function parseOptionalValue(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

function parsePositiveInteger(
  value: string | undefined,
  fallback: number,
): number {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function getDocsServerConfig(): DocsServerConfig {
  return {
    adminPassword: (process.env.DOCS_ADMIN_PASSWORD ?? '').trim(),
    sessionSecret: (process.env.DOCS_ADMIN_SESSION_SECRET ?? '').trim(),
    telemetryStorePath: (
      process.env.DOCS_TELEMETRY_STORE_PATH ?? '.telemetry/store.json'
    ).trim(),
    telemetryRetentionDays: parsePositiveInteger(
      process.env.DOCS_TELEMETRY_RETENTION_DAYS,
      30,
    ),
    telemetryMaxEvents: parsePositiveInteger(
      process.env.DOCS_TELEMETRY_MAX_EVENTS,
      2500,
    ),
    telemetryRedisRestUrl:
      parseOptionalValue(process.env.DOCS_TELEMETRY_REDIS_REST_URL) ??
      parseOptionalValue(process.env.UPSTASH_REDIS_REST_URL) ??
      parseOptionalValue(process.env.KV_REST_API_URL),
    telemetryRedisRestToken:
      parseOptionalValue(process.env.DOCS_TELEMETRY_REDIS_REST_TOKEN) ??
      parseOptionalValue(process.env.UPSTASH_REDIS_REST_TOKEN) ??
      parseOptionalValue(process.env.KV_REST_API_TOKEN),
    telemetryRedisKey:
      parseOptionalValue(process.env.DOCS_TELEMETRY_REDIS_KEY) ??
      'docs:telemetry:store',
    isProduction: process.env.NODE_ENV === 'production',
  };
}

export function isAdminConfigured(config = getDocsServerConfig()): boolean {
  return config.adminPassword.length > 0 && config.sessionSecret.length >= 16;
}

export function isPersistentTelemetryConfigured(
  config = getDocsServerConfig(),
): boolean {
  return Boolean(config.telemetryRedisRestUrl && config.telemetryRedisRestToken);
}

export function getTelemetryStorageDescription(
  config = getDocsServerConfig(),
): { adapter: 'upstash-redis' | 'filesystem'; target: string } {
  if (isPersistentTelemetryConfigured(config)) {
    return {
      adapter: 'upstash-redis',
      target: config.telemetryRedisKey,
    };
  }

  return {
    adapter: 'filesystem',
    target: config.telemetryStorePath,
  };
}