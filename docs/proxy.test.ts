import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === 'next/server') {
      return {
        shortCircuit: true,
        url: new URL('./node_modules/next/server.js', import.meta.url).href,
      };
    }
    if (specifier.startsWith('@/lib/server/')) {
      const moduleName = specifier.slice('@/lib/server/'.length);
      return {
        shortCircuit: true,
        url: new URL(`./lib/server/${moduleName}.ts`, import.meta.url).href,
      };
    }
    return nextResolve(specifier, context);
  },
});

type ProxyModule = typeof import('./proxy');
type SessionModule = typeof import('./lib/server/session');
type NextServerModule = typeof import('next/server');

const { proxy } = (await import(
  new URL('./proxy.ts', import.meta.url).href
)) as ProxyModule;
const { ADMIN_SESSION_COOKIE, createAdminSessionToken } = (await import(
  new URL('./lib/server/session.ts', import.meta.url).href
)) as SessionModule;
const { NextRequest } = (await import('next/server')) as NextServerModule;

const TEST_ONLY_SALT = Buffer.alloc(16, 1).toString('base64url');
const TEST_ONLY_HASH = Buffer.alloc(64, 2).toString('base64url');
const VALID_ADMIN_VERIFIER =
  `scrypt$16384$8$1$${TEST_ONLY_SALT}$${TEST_ONLY_HASH}`;
const ADMIN_SESSION_SECRET = 'test-only-admin-session-secret';
const ADMIN_ENVIRONMENT_KEYS = [
  'NODE_ENV',
  'DOCS_ADMIN_PASSWORD',
  'DOCS_ADMIN_SESSION_SECRET',
] as const;

async function withAdminEnvironment<T>(
  environment: Partial<Record<(typeof ADMIN_ENVIRONMENT_KEYS)[number], string>>,
  action: () => Promise<T>,
): Promise<T> {
  const previous = Object.fromEntries(
    ADMIN_ENVIRONMENT_KEYS.map((key) => [key, process.env[key]]),
  );
  for (const key of ADMIN_ENVIRONMENT_KEYS) {
    const value = environment[key];
    if (value === undefined) {
      delete process.env[key];
    } else {
      Reflect.set(process.env, key, value);
    }
  }

  try {
    return await action();
  } finally {
    for (const key of ADMIN_ENVIRONMENT_KEYS) {
      const value = previous[key];
      if (value === undefined) {
        delete process.env[key];
      } else {
        Reflect.set(process.env, key, value);
      }
    }
  }
}

function adminRequest(pathname: string, token?: string) {
  const headers = new Headers();
  if (token) {
    // Match NextResponse's cookie serializer: the wire value escapes the
    // percent-encoded token once, and NextRequest decodes it once on read.
    headers.set('cookie', `${ADMIN_SESSION_COOKIE}=${encodeURIComponent(token)}`);
  }
  return new NextRequest(new URL(pathname, 'https://docs.example'), { headers });
}

const proxyPath = fileURLToPath(new URL('./proxy.ts', import.meta.url));
const proxySource = ts.createSourceFile(
  proxyPath,
  readFileSync(proxyPath, 'utf8'),
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TS,
);

function findExportedConfig(): ts.ObjectLiteralExpression {
  for (const statement of proxySource.statements) {
    if (!ts.isVariableStatement(statement)) {
      continue;
    }

    const isExported = statement.modifiers?.some(
      (modifier) => modifier.kind === ts.SyntaxKind.ExportKeyword,
    );
    if (!isExported) {
      continue;
    }

    const declaration = statement.declarationList.declarations.find(
      (candidate) => ts.isIdentifier(candidate.name) && candidate.name.text === 'config',
    );
    if (declaration?.initializer && ts.isObjectLiteralExpression(declaration.initializer)) {
      return declaration.initializer;
    }
  }

  assert.fail('proxy.ts must export a config object');
}

function findConfigProperty(
  config: ts.ObjectLiteralExpression,
  name: string,
): ts.Expression {
  const property = config.properties.find(
    (candidate): candidate is ts.PropertyAssignment =>
      ts.isPropertyAssignment(candidate) &&
      ((ts.isIdentifier(candidate.name) && candidate.name.text === name) ||
        (ts.isStringLiteral(candidate.name) && candidate.name.text === name)),
  );

  assert.ok(property, `proxy config must define ${name}`);
  return property.initializer;
}

describe('proxy runtime contract', () => {
  const config = findExportedConfig();

  it('uses the Next 16 proxy convention without a legacy runtime override', () => {
    const source = readFileSync(proxyPath, 'utf8');
    assert.match(source, /export async function proxy/);
    assert.doesNotMatch(source, /export async function middleware/);
    assert.doesNotMatch(source, /runtime\s*:/);
  });

  it('continues to protect both admin route families', () => {
    const matcher = findConfigProperty(config, 'matcher');
    assert.ok(ts.isArrayLiteralExpression(matcher), 'matcher must be an array literal');

    const routes = matcher.elements.map((element) => {
      assert.ok(ts.isStringLiteral(element), 'each matcher must be a string literal');
      return element.text;
    });

    assert.deepEqual(routes, ['/admin/:path*', '/api/admin/:path*']);
  });

  it('uses explicit admin readiness rather than the deprecated credential shortcut', () => {
    const source = readFileSync(proxyPath, 'utf8');
    assert.match(source, /getAdminReadiness/);
    assert.doesNotMatch(source, /isAdminConfigured/);
  });
});

describe('proxy request behavior', { concurrency: false }, () => {
  it('keeps login and logout routes public when admin is unconfigured', async () => {
    await withAdminEnvironment({}, async () => {
      for (const pathname of [
        '/admin/login',
        '/api/admin/login',
        '/api/admin/logout',
      ]) {
        const response = await proxy(adminRequest(pathname));
        assert.equal(response.status, 200, pathname);
        assert.equal(response.headers.get('x-middleware-next'), '1', pathname);
      }
    });
  });

  it('reports unavailable admin page and API behavior when unconfigured', async () => {
    await withAdminEnvironment({}, async () => {
      const pageResponse = await proxy(adminRequest('/admin'));
      assert.equal(pageResponse.status, 307);
      assert.equal(
        pageResponse.headers.get('location'),
        'https://docs.example/admin/login?error=config',
      );

      const apiResponse = await proxy(adminRequest('/api/admin/telemetry'));
      assert.equal(apiResponse.status, 503);
      assert.deepEqual(await apiResponse.json(), {
        ok: false,
        code: 'config',
        error: 'Admin access is not configured.',
      });
    });
  });

  it('requires authentication when development admin is configured', async () => {
    await withAdminEnvironment(
      {
        NODE_ENV: 'development',
        DOCS_ADMIN_PASSWORD: VALID_ADMIN_VERIFIER,
        DOCS_ADMIN_SESSION_SECRET: ADMIN_SESSION_SECRET,
      },
      async () => {
        const pageResponse = await proxy(
          adminRequest('/admin/settings?window=7&view=errors'),
        );
        assert.equal(pageResponse.status, 307);
        assert.equal(
          pageResponse.headers.get('location'),
          'https://docs.example/admin/login?next=%2Fadmin%2Fsettings%3Fwindow%3D7%26view%3Derrors',
        );

        const apiResponse = await proxy(adminRequest('/api/admin/telemetry'));
        assert.equal(apiResponse.status, 401);
        assert.deepEqual(await apiResponse.json(), {
          ok: false,
          error: 'Authentication required.',
        });
      },
    );
  });

  it('reports a production limiter outage distinctly from missing credentials', async () => {
    await withAdminEnvironment(
      {
        NODE_ENV: 'production',
        DOCS_ADMIN_PASSWORD: VALID_ADMIN_VERIFIER,
        DOCS_ADMIN_SESSION_SECRET: ADMIN_SESSION_SECRET,
      },
      async () => {
        const pageResponse = await proxy(adminRequest('/admin'));
        assert.equal(pageResponse.status, 307);
        assert.equal(
          pageResponse.headers.get('location'),
          'https://docs.example/admin/login?error=limiter',
        );

        const apiResponse = await proxy(adminRequest('/api/admin/telemetry'));
        assert.equal(apiResponse.status, 503);
        assert.deepEqual(await apiResponse.json(), {
          ok: false,
          code: 'limiter',
          error: 'A production-safe distributed login limiter is unavailable.',
        });
      },
    );
  });

  it('passes authenticated admin page and API requests through', async () => {
    await withAdminEnvironment(
      {
        NODE_ENV: 'development',
        DOCS_ADMIN_PASSWORD: VALID_ADMIN_VERIFIER,
        DOCS_ADMIN_SESSION_SECRET: ADMIN_SESSION_SECRET,
      },
      async () => {
        const { token } = await createAdminSessionToken(
          ADMIN_SESSION_SECRET,
          60_000,
        );
        for (const pathname of ['/admin', '/api/admin/telemetry']) {
          const response = await proxy(adminRequest(pathname, token));
          assert.equal(response.status, 200, pathname);
          assert.equal(response.headers.get('x-middleware-next'), '1', pathname);
        }
      },
    );
  });
});
