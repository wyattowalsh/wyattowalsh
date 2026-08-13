import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

type AdminRateLimitModule = typeof import('./admin-rate-limit');
const {
  createMemoryAdminLoginRateLimiter,
  evaluateAdminLoginRateLimit,
  normalizeAdminLoginClientKey,
} = (await import(
  new URL('./admin-rate-limit.ts', import.meta.url).href
)) as AdminRateLimitModule;

describe('development admin login limiter', () => {
  it('bounds attempts and recovers after the window', () => {
    let now = 1_000;
    const limiter = createMemoryAdminLoginRateLimiter({
      maxAttempts: 2,
      windowMs: 100,
      now: () => now,
    });

    assert.deepEqual(limiter.check('client'), { allowed: true, remaining: 1 });
    assert.deepEqual(limiter.check('client'), { allowed: true, remaining: 0 });
    assert.deepEqual(limiter.check('client'), {
      allowed: false,
      reason: 'rate_limited',
      retryAfterMs: 100,
    });

    now += 100;
    assert.deepEqual(limiter.check('client'), { allowed: true, remaining: 1 });
  });

  it('evicts deterministically and never exceeds the key bound', () => {
    let now = 1_000;
    const limiter = createMemoryAdminLoginRateLimiter({
      maxKeys: 2,
      now: () => now,
    });

    limiter.check('bravo');
    limiter.check('alpha');
    now += 1;
    limiter.check('charlie');
    assert.equal(limiter.trackedKeyCount, 2);

    // The tie is broken lexically, so alpha was evicted and starts fresh.
    assert.deepEqual(limiter.check('alpha'), { allowed: true, remaining: 4 });
    assert.equal(limiter.trackedKeyCount, 2);
  });

  it('does not touch the memory limiter in production', () => {
    const limiter = {
      check(): never {
        throw new Error('memory limiter must not run');
      },
      trackedKeyCount: 0,
    };

    assert.deepEqual(
      evaluateAdminLoginRateLimit({
        clientKey: 'client',
        isProduction: true,
        limiter,
      }),
      { allowed: false, reason: 'distributed_limiter_required' },
    );
  });

  it('normalizes an untrusted forwarded client key to a bounded value', () => {
    assert.equal(normalizeAdminLoginClientKey(null), 'unknown');
    assert.equal(normalizeAdminLoginClientKey(' , second'), 'unknown');
    assert.equal(normalizeAdminLoginClientKey('first, second'), 'first');
    assert.equal(normalizeAdminLoginClientKey('x'.repeat(256)).length, 128);
  });
});
