import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

type AdminPasswordModule = typeof import('./admin-password');

const {
  hashAdminPassword,
  isAdminPasswordVerifier,
  verifyAdminPassword,
} = (await import(
  new URL('./admin-password.ts', import.meta.url).href
)) as AdminPasswordModule;

const validSalt = Buffer.alloc(16, 1).toString('base64url');
const validHash = Buffer.alloc(64, 2).toString('base64url');

function verifier(N: number, r: number, p: number): string {
  return `scrypt$${N}$${r}$${p}$${validSalt}$${validHash}`;
}

function verifierWithLengths(saltBytes: number, hashBytes: number): string {
  const salt = Buffer.alloc(saltBytes, 1).toString('base64url');
  const hash = Buffer.alloc(hashBytes, 2).toString('base64url');
  return `scrypt$1024$8$1$${salt}$${hash}`;
}

describe('admin-password scrypt KDF', () => {
  it('rejects plaintext and malformed verifiers', () => {
    assert.equal(isAdminPasswordVerifier(''), false);
    assert.equal(isAdminPasswordVerifier('plaintext-password'), false);
    assert.equal(isAdminPasswordVerifier('scrypt$not$enough'), false);
    assert.equal(
      isAdminPasswordVerifier('scrypt$3$8$1$aaaaaaaaaaaaaaaa$bbbbbbbbbbbbbbbb'),
      false,
    );
  });

  it('rejects unsafe cost, parallelization, and memory parameters', async () => {
    for (const unsafeVerifier of [
      verifier(512, 8, 1),
      verifier(1024, 33, 1),
      verifier(1024, 8, 17),
      verifier(65_536, 8, 1),
    ]) {
      assert.equal(isAdminPasswordVerifier(unsafeVerifier), false);
      assert.equal(await verifyAdminPassword('password', unsafeVerifier), false);
    }

    await assert.rejects(
      hashAdminPassword('password', { N: 512 }),
      /Invalid or unsafe scrypt parameters/,
    );
    await assert.rejects(
      hashAdminPassword('password', { N: 65_536, r: 8 }),
      /Invalid or unsafe scrypt parameters/,
    );
  });

  it('rejects salt and hash fields outside the emitted fixed lengths', async () => {
    for (const malformedVerifier of [
      verifierWithLengths(15, 64),
      verifierWithLengths(17, 64),
      verifierWithLengths(16, 63),
      verifierWithLengths(16, 65),
    ]) {
      assert.equal(isAdminPasswordVerifier(malformedVerifier), false);
      assert.equal(await verifyAdminPassword('password', malformedVerifier), false);
    }
  });

  it('hashes and verifies with timing-safe scrypt compare', async () => {
    const password = 'correct-horse-battery-staple';
    const verifier = await hashAdminPassword(password, { N: 1024 });

    assert.equal(isAdminPasswordVerifier(verifier), true);
    assert.match(verifier, /^scrypt\$1024\$8\$1\$/);
    assert.equal(await verifyAdminPassword(password, verifier), true);
    assert.equal(await verifyAdminPassword('wrong-password', verifier), false);
    assert.equal(await verifyAdminPassword('', verifier), false);
  });

  it('uses distinct salts per hash', async () => {
    const first = await hashAdminPassword('same-password', { N: 1024 });
    const second = await hashAdminPassword('same-password', { N: 1024 });
    assert.notEqual(first, second);
    assert.equal(await verifyAdminPassword('same-password', first), true);
    assert.equal(await verifyAdminPassword('same-password', second), true);
  });
});
