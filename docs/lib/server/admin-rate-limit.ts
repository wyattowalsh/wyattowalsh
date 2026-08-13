export type AdminRateLimitDecision =
  | {
      allowed: true;
      remaining: number;
    }
  | {
      allowed: false;
      reason: 'rate_limited' | 'distributed_limiter_required';
      retryAfterMs?: number;
    };

export type AdminLoginRateLimiter = {
  check(clientKey: string): AdminRateLimitDecision;
  readonly trackedKeyCount: number;
};

type MemoryAdminRateLimiterOptions = {
  windowMs?: number;
  maxAttempts?: number;
  maxKeys?: number;
  now?: () => number;
};

type AttemptWindow = {
  attempts: number[];
  lastSeen: number;
};

const DEFAULT_WINDOW_MS = 60_000;
const DEFAULT_MAX_ATTEMPTS = 5;
const DEFAULT_MAX_KEYS = 1_000;
const MAX_CLIENT_KEY_LENGTH = 128;

function requirePositiveInteger(value: number, name: string): void {
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new RangeError(`${name} must be a positive safe integer.`);
  }
}

export function normalizeAdminLoginClientKey(value: string | null): string {
  const firstForwardedValue = value?.split(',', 1)[0]?.trim();
  if (!firstForwardedValue) {
    return 'unknown';
  }

  return firstForwardedValue.slice(0, MAX_CLIENT_KEY_LENGTH);
}

/**
 * Build the bounded in-memory limiter used exclusively by local development.
 * Production callers are rejected by `evaluateAdminLoginRateLimit` before this
 * state can be touched.
 */
export function createMemoryAdminLoginRateLimiter(
  options: MemoryAdminRateLimiterOptions = {},
): AdminLoginRateLimiter {
  const windowMs = options.windowMs ?? DEFAULT_WINDOW_MS;
  const maxAttempts = options.maxAttempts ?? DEFAULT_MAX_ATTEMPTS;
  const maxKeys = options.maxKeys ?? DEFAULT_MAX_KEYS;
  const now = options.now ?? Date.now;
  requirePositiveInteger(windowMs, 'windowMs');
  requirePositiveInteger(maxAttempts, 'maxAttempts');
  requirePositiveInteger(maxKeys, 'maxKeys');

  const windows = new Map<string, AttemptWindow>();
  let lastObservedTime = Number.NEGATIVE_INFINITY;

  function observeTime(): number {
    const observed = now();
    if (!Number.isFinite(observed)) {
      throw new RangeError('Rate limiter clock must return a finite number.');
    }

    // A clock adjustment must not extend existing attempt windows indefinitely.
    lastObservedTime = Math.max(lastObservedTime, observed);
    return lastObservedTime;
  }

  function prune(currentTime: number): void {
    for (const [key, window] of windows) {
      window.attempts = window.attempts.filter(
        (attemptedAt) => currentTime - attemptedAt < windowMs,
      );
      if (window.attempts.length === 0) {
        windows.delete(key);
      }
    }
  }

  function evictOldestKey(): void {
    let oldest: { key: string; lastSeen: number } | undefined;
    for (const [key, window] of windows) {
      if (
        !oldest ||
        window.lastSeen < oldest.lastSeen ||
        (window.lastSeen === oldest.lastSeen && key < oldest.key)
      ) {
        oldest = { key, lastSeen: window.lastSeen };
      }
    }
    if (oldest) {
      windows.delete(oldest.key);
    }
  }

  return {
    check(clientKey: string): AdminRateLimitDecision {
      const currentTime = observeTime();
      prune(currentTime);
      const normalizedKey = normalizeAdminLoginClientKey(clientKey);
      const existing = windows.get(normalizedKey);
      const attempts = existing?.attempts ?? [];

      if (attempts.length >= maxAttempts) {
        return {
          allowed: false,
          reason: 'rate_limited',
          retryAfterMs: Math.max(1, windowMs - (currentTime - attempts[0])),
        };
      }

      if (!existing && windows.size >= maxKeys) {
        evictOldestKey();
      }
      attempts.push(currentTime);
      windows.set(normalizedKey, { attempts, lastSeen: currentTime });
      return { allowed: true, remaining: maxAttempts - attempts.length };
    },
    get trackedKeyCount(): number {
      return windows.size;
    },
  };
}

export function evaluateAdminLoginRateLimit(input: {
  clientKey: string;
  isProduction: boolean;
  limiter: AdminLoginRateLimiter;
}): AdminRateLimitDecision {
  if (input.isProduction) {
    return { allowed: false, reason: 'distributed_limiter_required' };
  }

  return input.limiter.check(input.clientKey);
}
