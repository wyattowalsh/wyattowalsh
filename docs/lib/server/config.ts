import { isAdminPasswordVerifier } from '@/lib/server/admin-password';

export type DocsServerConfig = {
  /** scrypt verifier from DOCS_ADMIN_PASSWORD — never plaintext. */
  adminPassword: string;
  sessionSecret: string;
  telemetryStorePath: string;
  telemetryRetentionDays: number;
  telemetryMaxEvents: number;
  isProduction: boolean;
};

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
    isProduction: process.env.NODE_ENV === 'production',
  };
}

export function isAdminConfigured(config = getDocsServerConfig()): boolean {
  return (
    isAdminPasswordVerifier(config.adminPassword) &&
    config.sessionSecret.length >= 16
  );
}

export function getTelemetryStorageDescription(
  config = getDocsServerConfig(),
): { adapter: 'filesystem'; target: string } {
  return {
    adapter: 'filesystem',
    target: config.telemetryStorePath,
  };
}