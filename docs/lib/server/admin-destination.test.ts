import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

type AdminDestinationModule = typeof import('./admin-destination');
const { parseAdminDestination } = (await import(
  new URL('./admin-destination.ts', import.meta.url).href
)) as AdminDestinationModule;

describe('admin redirect destinations', () => {
  it('accepts only the admin path boundary and preserves a safe query', () => {
    assert.equal(parseAdminDestination('/admin'), '/admin');
    assert.equal(parseAdminDestination('/admin/telemetry'), '/admin/telemetry');
    assert.equal(
      parseAdminDestination('/admin?window=30&view=errors'),
      '/admin?window=30&view=errors',
    );
    assert.equal(parseAdminDestination('/admin#ignored'), '/admin');
  });

  it('rejects cross-origin and ambiguous URL forms', () => {
    for (const unsafeDestination of [
      '/\\evil.example',
      '//evil.example/admin',
      'https://evil.example/admin',
      'admin',
      '/administrator',
      '/admin\\@evil.example',
      '/admin/%5cevil.example',
      '/admin/%2f%2fevil.example',
      '/admin/../outside',
    ]) {
      assert.equal(
        parseAdminDestination(unsafeDestination),
        '/admin',
        unsafeDestination,
      );
    }
  });

  it('uses the safe fallback for absent or excessively large input', () => {
    assert.equal(parseAdminDestination(undefined), '/admin');
    assert.equal(parseAdminDestination(null), '/admin');
    assert.equal(parseAdminDestination(''), '/admin');
    assert.equal(parseAdminDestination(`/admin?value=${'x'.repeat(2_048)}`), '/admin');
  });
});
