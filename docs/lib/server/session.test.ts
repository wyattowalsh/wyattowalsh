import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

type SessionModule = typeof import('./session');

const {
  ADMIN_SESSION_MAX_LIFETIME_MS,
  buildAdminSessionCookieOptions,
  createAdminSessionToken,
  verifyAdminSessionToken,
} = (await import(
  new URL('./session.ts', import.meta.url).href
)) as SessionModule;

const secret = 'test-session-secret-with-sufficient-entropy';

function toHex(bytes: ArrayBuffer): string {
  return Array.from(new Uint8Array(bytes), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

async function signPayload(payload: unknown): Promise<string> {
  const encodedPayload = encodeURIComponent(JSON.stringify(payload));
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const signature = await crypto.subtle.sign(
    'HMAC',
    key,
    new TextEncoder().encode(encodedPayload),
  );
  return `${encodedPayload}.${toHex(signature)}`;
}

describe('admin session tokens', () => {
  it('creates and verifies a bounded token', async () => {
    const lifetimeMs = 60_000;
    const { token, expiresAt } = await createAdminSessionToken(secret, lifetimeMs);
    const payload = await verifyAdminSessionToken(token, secret);

    assert.ok(payload);
    assert.equal(payload.role, 'admin');
    assert.equal(payload.expiresAt, expiresAt);
    assert.equal(payload.expiresAt - payload.issuedAt, lifetimeMs);
  });

  it('rejects invalid requested lifetimes before signing', async () => {
    for (const lifetimeMs of [
      0,
      -1,
      1.5,
      Number.POSITIVE_INFINITY,
      ADMIN_SESSION_MAX_LIFETIME_MS + 1,
    ]) {
      await assert.rejects(
        createAdminSessionToken(secret, lifetimeMs),
        /outside the allowed range/,
      );
    }
  });

  it('rejects signed tokens issued in the future', async () => {
    const issuedAt = Date.now() + 60_000;
    const token = await signPayload({
      role: 'admin',
      issuedAt,
      expiresAt: issuedAt + 60_000,
    });

    assert.equal(await verifyAdminSessionToken(token, secret), null);
  });

  it('rejects non-positive and excessive signed lifetimes', async () => {
    const issuedAt = Date.now() - 1_000;
    const nonPositiveToken = await signPayload({
      role: 'admin',
      issuedAt,
      expiresAt: issuedAt,
    });
    const excessiveToken = await signPayload({
      role: 'admin',
      issuedAt,
      expiresAt: issuedAt + ADMIN_SESSION_MAX_LIFETIME_MS + 1,
    });

    assert.equal(await verifyAdminSessionToken(nonPositiveToken, secret), null);
    assert.equal(await verifyAdminSessionToken(excessiveToken, secret), null);
  });

  it('rejects expired, malformed, and tampered tokens', async () => {
    const issuedAt = Date.now() - 120_000;
    const expiredToken = await signPayload({
      role: 'admin',
      issuedAt,
      expiresAt: issuedAt + 60_000,
    });
    const { token } = await createAdminSessionToken(secret, 60_000);
    const replacement = token.endsWith('a') ? 'b' : 'a';
    const tamperedToken = `${token.slice(0, -1)}${replacement}`;

    assert.equal(await verifyAdminSessionToken(expiredToken, secret), null);
    assert.equal(await verifyAdminSessionToken('not-a-token', secret), null);
    assert.equal(await verifyAdminSessionToken(tamperedToken, secret), null);
  });

  it('builds secure production-only cookie options', () => {
    const expiresAt = Date.now() + 60_000;
    assert.deepEqual(buildAdminSessionCookieOptions(false, expiresAt), {
      httpOnly: true,
      sameSite: 'lax',
      secure: false,
      path: '/',
      expires: new Date(expiresAt),
    });
    assert.equal(buildAdminSessionCookieOptions(true, expiresAt).secure, true);
  });
});
