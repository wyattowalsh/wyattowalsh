import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';

const adminAuthPath = fileURLToPath(
  new URL('./admin-auth.ts', import.meta.url),
);
const loginRoutePath = fileURLToPath(
  new URL('../../app/api/admin/login/route.ts', import.meta.url),
);
const searchRoutePath = fileURLToPath(
  new URL('../../app/api/search/route.ts', import.meta.url),
);

describe('admin runtime fail-closed contracts', () => {
  it('requires full readiness before accepting an existing session', () => {
    const source = readFileSync(adminAuthPath, 'utf8');
    const sessionFunction = source.slice(
      source.indexOf('export async function getValidatedAdminSession'),
      source.indexOf('export async function requireAdminSession'),
    );

    assert.match(sessionFunction, /getAdminReadiness\(config\)\.available/);
    assert.doesNotMatch(sessionFunction, /isAdminConfigured/);
  });

  it('keeps the route binding thin around the behavior-tested login handler', () => {
    const source = readFileSync(loginRoutePath, 'utf8');

    assert.match(source, /handleAdminLogin\(request/);
    assert.match(source, /recordObservation:\s*recordLoginObservation/);
    assert.doesNotMatch(source, /NextResponse\.(?:json|redirect)/);
  });

  it('records a bounded search failure reason instead of raw exception messages', () => {
    const searchSource = readFileSync(searchRoutePath, 'utf8');

    assert.doesNotMatch(searchSource, /error instanceof Error \? error\.message/);
    assert.match(searchSource, /Docs search operation failed\./);
  });
});
