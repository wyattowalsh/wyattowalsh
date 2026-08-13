import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { describe, it } from 'node:test';

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith('@/lib/server/')) {
      const moduleName = specifier.slice('@/lib/server/'.length);
      return {
        shortCircuit: true,
        url: new URL(`./${moduleName}.ts`, import.meta.url).href,
      };
    }
    return nextResolve(specifier, context);
  },
});

type ConfigModule = typeof import('./config');
const {
  getAdminReadiness,
  getDocsServerConfig,
  getTelemetryStorageDescription,
  hasAdminCredentials,
  isAdminConfigured,
} = (await import(
  new URL('./config.ts', import.meta.url).href
)) as ConfigModule;

const TEST_ONLY_SALT = Buffer.alloc(16, 1).toString('base64url');
const TEST_ONLY_HASH = Buffer.alloc(64, 2).toString('base64url');
const VALID_VERIFIER =
  `scrypt$16384$8$1$${TEST_ONLY_SALT}$${TEST_ONLY_HASH}`;
const SESSION_SECRET = 'test-only-session-secret';

describe('docs server config', () => {
  it('defaults development to filesystem and production to disabled', () => {
    const development = getDocsServerConfig({});
    assert.equal(development.telemetryBackend, 'filesystem');
    assert.deepEqual(getTelemetryStorageDescription(development), {
      adapter: 'filesystem',
      availability: 'available',
      target: 'Local filesystem',
    });

    const production = getDocsServerConfig({ NODE_ENV: 'production' });
    assert.equal(production.telemetryBackend, 'disabled');
    assert.deepEqual(getTelemetryStorageDescription(production), {
      adapter: 'disabled',
      availability: 'disabled',
      target: 'Custom telemetry disabled',
    });
  });

  it('fails invalid backend values closed without exposing the value', () => {
    const config = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_TELEMETRY_BACKEND: 'surprise-backend',
    });
    assert.equal(config.telemetryBackend, 'disabled');
    assert.equal(config.telemetryConfigurationIssue, 'invalid_backend');
    assert.deepEqual(getTelemetryStorageDescription(config), {
      adapter: 'disabled',
      availability: 'unavailable',
      target: 'Custom telemetry disabled',
    });
  });

  it('accepts only complete positive safe integers for numeric limits', () => {
    for (const invalid of ['0', '-1', '1.5', '1e6', '30days', '9007199254740992']) {
      const config = getDocsServerConfig({
        DOCS_TELEMETRY_RETENTION_DAYS: invalid,
        DOCS_TELEMETRY_MAX_EVENTS: invalid,
      });
      assert.equal(config.telemetryRetentionDays, 30);
      assert.equal(config.telemetryMaxEvents, 2500);
    }

    const config = getDocsServerConfig({
      DOCS_TELEMETRY_RETENTION_DAYS: ' 45 ',
      DOCS_TELEMETRY_MAX_EVENTS: '5000',
    });
    assert.equal(config.telemetryRetentionDays, 45);
    assert.equal(config.telemetryMaxEvents, 5000);
  });

  it('rejects the single-process filesystem backend in production', () => {
    const config = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_TELEMETRY_BACKEND: 'filesystem',
      DOCS_TELEMETRY_STORE_PATH: '/tmp/must-not-be-exposed.json',
    });
    assert.equal(config.telemetryBackend, 'disabled');
    assert.equal(
      config.telemetryConfigurationIssue,
      'filesystem_not_production',
    );
    const description = getTelemetryStorageDescription(config);
    assert.deepEqual(description, {
      adapter: 'disabled',
      availability: 'unavailable',
      target: 'Custom telemetry disabled',
    });
    assert.doesNotMatch(JSON.stringify(description), /must-not-be-exposed/);
  });

  it('requires explicit, complete Redis configuration and stays redacted', () => {
    const incomplete = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_TELEMETRY_BACKEND: 'redis',
      DOCS_TELEMETRY_REDIS_REST_URL: 'https://redis.example',
    });
    assert.equal(incomplete.telemetryConfigurationIssue, 'redis_credentials_missing');
    assert.deepEqual(getTelemetryStorageDescription(incomplete), {
      adapter: 'redis',
      availability: 'unavailable',
      target: 'Redis configuration incomplete',
    });

    const complete = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_TELEMETRY_BACKEND: 'redis',
      DOCS_TELEMETRY_REDIS_REST_URL: 'https://redis.example',
      DOCS_TELEMETRY_REDIS_REST_TOKEN: 'secret-token',
      DOCS_TELEMETRY_REDIS_KEY: 'private-key-name',
    });
    const description = getTelemetryStorageDescription(complete);
    assert.equal(complete.telemetryConfigurationIssue, undefined);
    assert.deepEqual(description, {
      adapter: 'redis',
      availability: 'unavailable',
      target: 'Redis adapter unavailable',
    });
    assert.doesNotMatch(JSON.stringify(description), /redis\.example|secret-token|private-key-name/);
  });

  it('separates credentials from production admin readiness', () => {
    const development = getDocsServerConfig({
      DOCS_ADMIN_PASSWORD: VALID_VERIFIER,
      DOCS_ADMIN_SESSION_SECRET: SESSION_SECRET,
    });
    assert.equal(hasAdminCredentials(development), true);
    assert.deepEqual(getAdminReadiness(development), {
      available: true,
      limiter: 'memory',
    });
    assert.equal(isAdminConfigured(development), true);

    const production = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_ADMIN_PASSWORD: VALID_VERIFIER,
      DOCS_ADMIN_SESSION_SECRET: SESSION_SECRET,
    });
    assert.equal(hasAdminCredentials(production), true);
    assert.deepEqual(getAdminReadiness(production), {
      available: false,
      limiter: 'disabled',
      reason: 'distributed_limiter_missing',
    });
    assert.deepEqual(
      getAdminReadiness(production, {
        distributedRateLimiterAvailable: true,
      }),
      { available: true, limiter: 'redis' },
    );
    assert.equal(isAdminConfigured(production), false);
  });

  it('rejects malformed credentials before limiter readiness', () => {
    const config = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_ADMIN_PASSWORD: 'plaintext',
      DOCS_ADMIN_SESSION_SECRET: SESSION_SECRET,
    });
    assert.equal(hasAdminCredentials(config), false);
    assert.deepEqual(getAdminReadiness(config), {
      available: false,
      limiter: 'disabled',
      reason: 'credentials_missing',
    });
  });
});
