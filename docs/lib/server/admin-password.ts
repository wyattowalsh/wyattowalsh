import { randomBytes, scrypt, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';

/**
 * DOCS_ADMIN_PASSWORD must store a scrypt verifier — never a plaintext password.
 *
 * Format: scrypt$<N>$<r>$<p>$<salt_b64url>$<hash_b64url>
 * Example mint: `await hashAdminPassword('your-password')` (Node/runtime only).
 */
const scryptAsync = promisify(scrypt);

export const ADMIN_PASSWORD_KDF = 'scrypt' as const;

const DEFAULT_N = 16_384;
const DEFAULT_R = 8;
const DEFAULT_P = 1;
const KEY_LENGTH = 64;
const SALT_BYTES = 16;
/** 128 * N * r for default params is 16 MiB; leave headroom above Node's 32 MiB default. */
const MAX_MEM = 64 * 1024 * 1024;

const VERIFIER_PATTERN =
  /^scrypt\$(\d+)\$(\d+)\$(\d+)\$([A-Za-z0-9_-]+)\$([A-Za-z0-9_-]+)$/;

export function isAdminPasswordVerifier(value: string): boolean {
  if (!VERIFIER_PATTERN.test(value)) {
    return false;
  }

  const parsed = parseAdminPasswordVerifier(value);
  return parsed !== null;
}

function parseAdminPasswordVerifier(value: string): {
  N: number;
  r: number;
  p: number;
  salt: Buffer;
  hash: Buffer;
} | null {
  const match = VERIFIER_PATTERN.exec(value);
  if (!match) {
    return null;
  }

  const N = Number(match[1]);
  const r = Number(match[2]);
  const p = Number(match[3]);
  if (
    !Number.isInteger(N) ||
    !Number.isInteger(r) ||
    !Number.isInteger(p) ||
    N < 2 ||
    (N & (N - 1)) !== 0 ||
    r < 1 ||
    p < 1
  ) {
    return null;
  }

  try {
    const salt = Buffer.from(match[4], 'base64url');
    const hash = Buffer.from(match[5], 'base64url');
    if (salt.length < 16 || hash.length < 16) {
      return null;
    }
    return { N, r, p, salt, hash };
  } catch {
    return null;
  }
}

export async function hashAdminPassword(
  password: string,
  options?: { N?: number; r?: number; p?: number },
): Promise<string> {
  if (password.length === 0) {
    throw new Error('Admin password must be non-empty.');
  }

  const N = options?.N ?? DEFAULT_N;
  const r = options?.r ?? DEFAULT_R;
  const p = options?.p ?? DEFAULT_P;
  const salt = randomBytes(SALT_BYTES);
  const derived = (await scryptAsync(password, salt, KEY_LENGTH, {
    N,
    r,
    p,
    maxmem: MAX_MEM,
  })) as Buffer;

  return [
    ADMIN_PASSWORD_KDF,
    String(N),
    String(r),
    String(p),
    salt.toString('base64url'),
    derived.toString('base64url'),
  ].join('$');
}

export async function verifyAdminPassword(
  password: string,
  storedVerifier: string,
): Promise<boolean> {
  const parsed = parseAdminPasswordVerifier(storedVerifier);
  if (!parsed || password.length === 0) {
    return false;
  }

  const derived = (await scryptAsync(password, parsed.salt, parsed.hash.length, {
    N: parsed.N,
    r: parsed.r,
    p: parsed.p,
    maxmem: MAX_MEM,
  })) as Buffer;

  if (derived.length !== parsed.hash.length) {
    return false;
  }

  return timingSafeEqual(derived, parsed.hash);
}
