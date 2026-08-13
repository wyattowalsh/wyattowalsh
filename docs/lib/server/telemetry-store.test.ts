import assert from 'node:assert/strict';
import {
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  rename,
  rm,
  unlink,
  writeFile,
} from 'node:fs/promises';
import { registerHooks } from 'node:module';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { describe, it } from 'node:test';

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === 'server-only') {
      return {
        shortCircuit: true,
        url: 'data:text/javascript,export {};',
      };
    }
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
type TelemetryStoreModule = typeof import('./telemetry-store');
const { getDocsServerConfig } = (await import(
  new URL('./config.ts', import.meta.url).href
)) as ConfigModule;
const {
  createTelemetryService,
  TelemetryStoreUnavailableError,
} = (await import(
  new URL('./telemetry-store.ts', import.meta.url).href
)) as TelemetryStoreModule;

const NOW = Date.parse('2026-08-12T12:00:00.000Z');

function idFactory() {
  let index = 0;
  return () => `generated-${(index += 1)}`;
}

async function temporaryDirectory(): Promise<string> {
  return mkdtemp(path.join(tmpdir(), 'wyattowalsh-telemetry-'));
}

describe('telemetry store service', () => {
  it('keeps disabled mode truthful without touching the filesystem', async () => {
    let fileSystemCalls = 0;
    const inaccessibleFileSystem = {
      async mkdir() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
      async readFile() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
      async writeFile() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
      async rename() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
      async unlink() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
    };
    const config = getDocsServerConfig({ NODE_ENV: 'production' });
    const service = createTelemetryService(config, {
      fileSystem: inaccessibleFileSystem,
      now: () => NOW,
      createId: idFactory(),
    });

    assert.deepEqual(
      await service.recordEvents([{ name: 'page_view', source: 'client' }]),
      { mode: 'disabled', received: 1, stored: 0 },
    );
    const snapshot = await service.getDashboardSnapshot(7);
    assert.equal(snapshot.adapter, 'disabled');
    assert.equal(snapshot.availability, 'disabled');
    assert.equal(snapshot.unavailableReason, 'disabled');
    assert.equal(snapshot.totalRetainedEvents, 0);
    assert.equal(fileSystemCalls, 0);
  });

  it('reports a production filesystem override as unavailable configuration', async () => {
    let fileSystemCalls = 0;
    const inaccessibleFileSystem = {
      async mkdir() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
      async readFile() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
      async writeFile() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
      async rename() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
      async unlink() {
        fileSystemCalls += 1;
        throw new Error('filesystem must not be used');
      },
    };
    const config = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_TELEMETRY_BACKEND: 'filesystem',
      DOCS_TELEMETRY_STORE_PATH: '/tmp/must-not-be-used.json',
    });
    const service = createTelemetryService(config, {
      fileSystem: inaccessibleFileSystem,
      now: () => NOW,
      createId: idFactory(),
    });

    assert.deepEqual(
      await service.recordEvents([{ name: 'page_view', source: 'client' }]),
      { mode: 'disabled', received: 1, stored: 0 },
    );
    const snapshot = await service.getDashboardSnapshot(7);
    assert.equal(snapshot.adapter, 'disabled');
    assert.equal(snapshot.availability, 'unavailable');
    assert.equal(snapshot.unavailableReason, 'configuration');
    assert.equal(snapshot.storageTarget, 'Custom telemetry disabled');
    assert.equal(fileSystemCalls, 0);
  });

  it('writes one normalized, pruned, capped batch via atomic replacement', async () => {
    const directory = await temporaryDirectory();
    try {
      const config = getDocsServerConfig({
        DOCS_TELEMETRY_BACKEND: 'filesystem',
        DOCS_TELEMETRY_STORE_PATH: 'state/store.json',
        DOCS_TELEMETRY_RETENTION_DAYS: '2',
        DOCS_TELEMETRY_MAX_EVENTS: '2',
      });
      const service = createTelemetryService(config, {
        cwd: directory,
        now: () => NOW,
        createId: idFactory(),
      });
      const result = await service.recordEvents([
        {
          name: 'page_view',
          source: 'server',
          occurredAt: '2026-08-01T12:00:00.000Z',
        },
        {
          name: 'page_view',
          source: 'server',
          occurredAt: '2026-08-12T10:00:00.000Z',
        },
        {
          name: 'docs_search',
          source: 'server',
          occurredAt: '2026-08-12T11:00:00.000Z',
          searchQuery: 'telemetry',
        },
      ]);

      assert.deepEqual(result, {
        mode: 'filesystem',
        received: 3,
        stored: 2,
      });
      const storePath = path.join(directory, 'state', 'store.json');
      const persisted = JSON.parse(await readFile(storePath, 'utf8')) as {
        version: number;
        events: Array<{ name: string }>;
      };
      assert.equal(persisted.version, 1);
      assert.deepEqual(
        persisted.events.map((event) => event.name),
        ['page_view', 'docs_search'],
      );
      assert.deepEqual(await readdir(path.dirname(storePath)), ['store.json']);

      const snapshot = await service.getDashboardSnapshot(1);
      assert.equal(snapshot.availability, 'available');
      assert.equal(snapshot.storageTarget, 'Local filesystem');
      assert.equal(snapshot.totalRetainedEvents, 2);
      assert.equal(snapshot.summary.searches, 1);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it('does not poison later queued writes after one failure', async () => {
    const directory = await temporaryDirectory();
    let failNextWrite = true;
    try {
      const fileSystem = {
        async mkdir(directoryPath: string) {
          await mkdir(directoryPath, { recursive: true });
        },
        async readFile(filePath: string) {
          return readFile(filePath, 'utf8');
        },
        async writeFile(filePath: string, content: string) {
          if (failNextWrite) {
            failNextWrite = false;
            throw Object.assign(new Error('injected failure'), { code: 'EIO' });
          }
          await writeFile(filePath, content, {
            encoding: 'utf8',
            flag: 'wx',
          });
        },
        async rename(from: string, to: string) {
          await rename(from, to);
        },
        async unlink(filePath: string) {
          await unlink(filePath);
        },
      };
      const config = getDocsServerConfig({
        DOCS_TELEMETRY_BACKEND: 'filesystem',
        DOCS_TELEMETRY_STORE_PATH: 'store.json',
      });
      const service = createTelemetryService(config, {
        cwd: directory,
        fileSystem,
        now: () => NOW,
        createId: idFactory(),
      });

      await assert.rejects(
        service.recordEvents([{ name: 'page_view', source: 'server' }]),
        /injected failure/,
      );
      assert.deepEqual(
        await service.recordEvents([{ name: 'docs_search', source: 'server' }]),
        { mode: 'filesystem', received: 1, stored: 1 },
      );
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it('preserves an existing valid store when replacement fails', async () => {
    const directory = await temporaryDirectory();
    try {
      const config = getDocsServerConfig({
        DOCS_TELEMETRY_BACKEND: 'filesystem',
        DOCS_TELEMETRY_STORE_PATH: 'store.json',
      });
      const seedService = createTelemetryService(config, {
        cwd: directory,
        now: () => NOW,
        createId: idFactory(),
      });
      await seedService.recordEvents([
        { name: 'page_view', source: 'server', pathname: '/prior' },
      ]);

      const storePath = path.join(directory, 'store.json');
      const priorContent = await readFile(storePath, 'utf8');
      const replacementFailureService = createTelemetryService(config, {
        cwd: directory,
        now: () => NOW,
        createId: idFactory(),
        fileSystem: {
          async mkdir(directoryPath: string) {
            await mkdir(directoryPath, { recursive: true });
          },
          async readFile(filePath: string) {
            return readFile(filePath, 'utf8');
          },
          async writeFile(filePath: string, content: string) {
            await writeFile(filePath, content, {
              encoding: 'utf8',
              flag: 'wx',
              mode: 0o600,
            });
          },
          async rename() {
            throw new Error('injected replacement failure');
          },
          async unlink(filePath: string) {
            await unlink(filePath);
          },
        },
      });

      await assert.rejects(
        replacementFailureService.recordEvents([
          { name: 'docs_search', source: 'server', searchQuery: 'new' },
        ]),
        /injected replacement failure/,
      );
      assert.equal(await readFile(storePath, 'utf8'), priorContent);
      assert.deepEqual(await readdir(directory), ['store.json']);

      const snapshot = await replacementFailureService.getDashboardSnapshot(7);
      assert.equal(snapshot.availability, 'available');
      assert.equal(snapshot.totalRetainedEvents, 1);
      assert.equal(snapshot.recentEvents[0]?.pathname, '/prior');
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it('serializes concurrent local writes without losing events', async () => {
    const directory = await temporaryDirectory();
    try {
      const config = getDocsServerConfig({
        DOCS_TELEMETRY_BACKEND: 'filesystem',
        DOCS_TELEMETRY_STORE_PATH: 'store.json',
        DOCS_TELEMETRY_MAX_EVENTS: '32',
      });
      const service = createTelemetryService(config, {
        cwd: directory,
        now: () => NOW,
        createId: idFactory(),
      });
      const pathnames = Array.from({ length: 12 }, (_, index) => `/docs/${index}`);

      const results = await Promise.all(
        pathnames.map((pathname) =>
          service.recordEvents([{ name: 'page_view', source: 'server', pathname }]),
        ),
      );

      assert.equal(results.length, pathnames.length);
      assert.ok(results.every((result) => result.stored === 1));
      const persisted = JSON.parse(
        await readFile(path.join(directory, 'store.json'), 'utf8'),
      ) as { events: Array<{ pathname?: string }> };
      assert.deepEqual(
        persisted.events.map((event) => event.pathname).sort(),
        [...pathnames].sort(),
      );
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it('surfaces corruption and non-ENOENT read failures', async () => {
    const directory = await temporaryDirectory();
    try {
      const storePath = path.join(directory, 'store.json');
      await writeFile(storePath, '{not-json', 'utf8');
      const config = getDocsServerConfig({
        DOCS_TELEMETRY_BACKEND: 'filesystem',
        DOCS_TELEMETRY_STORE_PATH: 'store.json',
      });
      const corruptService = createTelemetryService(config, {
        cwd: directory,
        now: () => NOW,
        createId: idFactory(),
      });
      await assert.rejects(
        corruptService.recordEvents([{ name: 'page_view', source: 'server' }]),
        TelemetryStoreUnavailableError,
      );
      const corruptSnapshot = await corruptService.getDashboardSnapshot(7);
      assert.equal(corruptSnapshot.availability, 'unavailable');
      assert.equal(corruptSnapshot.unavailableReason, 'backend');

      const permissionService = createTelemetryService(config, {
        cwd: directory,
        now: () => NOW,
        createId: idFactory(),
        fileSystem: {
          async mkdir() {},
          async readFile() {
            throw Object.assign(new Error('denied'), { code: 'EACCES' });
          },
          async writeFile() {},
          async rename() {},
          async unlink() {},
        },
      });
      await assert.rejects(
        permissionService.recordEvents([{ name: 'page_view', source: 'server' }]),
        /denied/,
      );
      const permissionSnapshot = await permissionService.getDashboardSnapshot(7);
      assert.equal(permissionSnapshot.availability, 'unavailable');
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it('rejects structurally invalid persisted events', async () => {
    const directory = await temporaryDirectory();
    try {
      await writeFile(
        path.join(directory, 'store.json'),
        JSON.stringify({ version: 1, events: [{ name: 'page_view' }] }),
        'utf8',
      );
      const config = getDocsServerConfig({
        DOCS_TELEMETRY_BACKEND: 'filesystem',
        DOCS_TELEMETRY_STORE_PATH: 'store.json',
      });
      const service = createTelemetryService(config, {
        cwd: directory,
        now: () => NOW,
        createId: idFactory(),
      });
      await assert.rejects(
        service.recordEvents([{ name: 'page_view', source: 'server' }]),
        /Telemetry store data is invalid/,
      );
      assert.equal(
        (await service.getDashboardSnapshot(7)).availability,
        'unavailable',
      );
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it('keeps explicit Redis mode unavailable without configuration or an adapter', async () => {
    const incomplete = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_TELEMETRY_BACKEND: 'redis',
    });
    const incompleteService = createTelemetryService(incomplete, {
      now: () => NOW,
      createId: idFactory(),
    });
    await assert.rejects(
      incompleteService.recordEvents([{ name: 'page_view', source: 'server' }]),
      TelemetryStoreUnavailableError,
    );
    assert.equal(
      (await incompleteService.getDashboardSnapshot(7)).unavailableReason,
      'configuration',
    );

    const configured = getDocsServerConfig({
      NODE_ENV: 'production',
      DOCS_TELEMETRY_BACKEND: 'redis',
      DOCS_TELEMETRY_REDIS_REST_URL: 'https://redis.example',
      DOCS_TELEMETRY_REDIS_REST_TOKEN: 'secret-token',
    });
    const configuredService = createTelemetryService(configured, {
      now: () => NOW,
      createId: idFactory(),
    });
    await assert.rejects(
      configuredService.recordEvents([{ name: 'page_view', source: 'server' }]),
      TelemetryStoreUnavailableError,
    );
    const snapshot = await configuredService.getDashboardSnapshot(7);
    assert.equal(snapshot.adapter, 'redis');
    assert.equal(snapshot.availability, 'unavailable');
    assert.equal(snapshot.unavailableReason, 'backend');
    assert.doesNotMatch(JSON.stringify(snapshot), /redis\.example|secret-token/);
  });
});
