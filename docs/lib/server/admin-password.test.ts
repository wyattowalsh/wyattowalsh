import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  hashAdminPassword,
  isAdminPasswordVerifier,
  verifyAdminPassword,
} from './admin-password.ts';

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
