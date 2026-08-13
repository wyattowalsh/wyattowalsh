import { isAdminPasswordVerifier } from '@/lib/server/admin-password';
import type { TelemetryBackend } from '@/lib/server/telemetry-core';

export type TelemetryConfigurationIssue =
  | 'invalid_backend'
  | 'filesystem_not_production'
  | 'redis_credentials_missing';

export type AdminReadiness =
  | { available: true; limiter: 'memory' | 'redis' }
  | {
      available: false;
      limiter: 'disabled' | 'redis';
      reason:
        | 'credentials_missing'
        | 'distributed_limiter_missing'
        | 'redis_configuration_invalid';
    };

export type DocsServerConfig = {
  /** scrypt verifier from DOCS_ADMIN_PASSWORD — never plaintext. */
  adminPassword: string;
  sessionSecret: string;
  telemetryBackend: TelemetryBackend;
  telemetryConfigurationIssue?: TelemetryConfigurationIssue;
  telemetryStorePath: string;
  telemetryRetentionDays: number;
  telemetryMaxEvents: number;
  telemetryRedisRestUrl?: string;
  telemetryRedisRestToken?: string;
  telemetryRedisKey: string;
  isProduction: boolean;
};

export type TelemetryStorageDescription = {
  adapter: TelemetryBackend;
  availability: 'available' | 'disabled' | 'unavailable';
  /** A deliberately redacted, user-facing target description. */
  target: string;
};

function parseOptionalValue(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

function parsePositiveInteger(
  value: string | undefined,
  fallback: number,
): number {
  const normalized = value?.trim() ?? '';
  if (!/^[1-9]\d*$/.test(normalized)) {
    return fallback;
  }
  const parsed = Number(normalized);
  return Number.isSafeInteger(parsed) ? parsed : fallback;
}

function resolveTelemetryBackend(
  value: string | undefined,
  isProduction: boolean,
): {
  backend: TelemetryBackend;
  issue?: TelemetryConfigurationIssue;
} {
  const normalized = value?.trim().toLowerCase();
  if (!normalized) {
    return { backend: isProduction ? 'disabled' : 'filesystem' };
  }

  if (
    normalized === 'disabled' ||
    normalized === 'filesystem' ||
    normalized === 'redis'
  ) {
    if (isProduction && normalized === 'filesystem') {
      return { backend: 'disabled', issue: 'filesystem_not_production' };
    }
    return { backend: normalized };
  }

  // Invalid production configuration must not accidentally enable local storage.
  return { backend: 'disabled', issue: 'invalid_backend' };
}

export function getDocsServerConfig(
  environment: Readonly<Record<string, string | undefined>> = process.env,
): DocsServerConfig {
  const isProduction = environment.NODE_ENV === 'production';
  const resolvedBackend = resolveTelemetryBackend(
    environment.DOCS_TELEMETRY_BACKEND,
    isProduction,
  );
  const telemetryRedisRestUrl = parseOptionalValue(
    environment.DOCS_TELEMETRY_REDIS_REST_URL,
  );
  const telemetryRedisRestToken = parseOptionalValue(
    environment.DOCS_TELEMETRY_REDIS_REST_TOKEN,
  );
  const redisCredentialsComplete = Boolean(
    telemetryRedisRestUrl && telemetryRedisRestToken,
  );
  const telemetryConfigurationIssue =
    resolvedBackend.issue ??
    (resolvedBackend.backend === 'redis' && !redisCredentialsComplete
      ? 'redis_credentials_missing'
      : undefined);

  return {
    adminPassword: (environment.DOCS_ADMIN_PASSWORD ?? '').trim(),
    sessionSecret: (environment.DOCS_ADMIN_SESSION_SECRET ?? '').trim(),
    telemetryBackend: resolvedBackend.backend,
    telemetryConfigurationIssue,
    telemetryStorePath:
      parseOptionalValue(environment.DOCS_TELEMETRY_STORE_PATH) ??
      '.telemetry/store.json',
    telemetryRetentionDays: parsePositiveInteger(
      environment.DOCS_TELEMETRY_RETENTION_DAYS,
      30,
    ),
    telemetryMaxEvents: parsePositiveInteger(
      environment.DOCS_TELEMETRY_MAX_EVENTS,
      2500,
    ),
    telemetryRedisRestUrl,
    telemetryRedisRestToken,
    telemetryRedisKey:
      parseOptionalValue(environment.DOCS_TELEMETRY_REDIS_KEY) ??
      'docs:telemetry:events',
    isProduction,
  };
}

export function hasAdminCredentials(
  config = getDocsServerConfig(),
): boolean {
  return (
    isAdminPasswordVerifier(config.adminPassword) &&
    config.sessionSecret.length >= 16
  );
}

/**
 * Report whether admin login can be offered safely.
 *
 * The Redis limiter is deliberately dependency-injected. Until the approved
 * adapter exists and calls this function with `distributedRateLimiterAvailable`,
 * production remains fail-closed.
 */
export function getAdminReadiness(
  config = getDocsServerConfig(),
  options: { distributedRateLimiterAvailable?: boolean } = {},
): AdminReadiness {
  if (!hasAdminCredentials(config)) {
    return {
      available: false,
      limiter: 'disabled',
      reason: 'credentials_missing',
    };
  }

  if (!config.isProduction) {
    return { available: true, limiter: 'memory' };
  }

  if (config.telemetryConfigurationIssue === 'redis_credentials_missing') {
    return {
      available: false,
      limiter: 'redis',
      reason: 'redis_configuration_invalid',
    };
  }

  if (options.distributedRateLimiterAvailable) {
    return { available: true, limiter: 'redis' };
  }

  return {
    available: false,
    limiter: 'disabled',
    reason: 'distributed_limiter_missing',
  };
}

/** @deprecated Prefer `hasAdminCredentials` or `getAdminReadiness`. */
export function isAdminConfigured(config = getDocsServerConfig()): boolean {
  return getAdminReadiness(config).available;
}

export function getTelemetryStorageDescription(
  config = getDocsServerConfig(),
): TelemetryStorageDescription {
  if (config.telemetryBackend === 'disabled') {
    return {
      adapter: 'disabled',
      availability:
        config.telemetryConfigurationIssue === 'invalid_backend' ||
        config.telemetryConfigurationIssue === 'filesystem_not_production'
          ? 'unavailable'
          : 'disabled',
      target: 'Custom telemetry disabled',
    };
  }

  if (config.telemetryBackend === 'redis') {
    return {
      adapter: 'redis',
      availability: 'unavailable',
      target: config.telemetryConfigurationIssue
        ? 'Redis configuration incomplete'
        : 'Redis adapter unavailable',
    };
  }

  return {
    adapter: 'filesystem',
    availability: 'available',
    target: 'Local filesystem',
  };
}
