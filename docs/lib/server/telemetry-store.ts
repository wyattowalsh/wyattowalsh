import 'server-only';

import {
  mkdir,
  readFile,
  rename,
  unlink,
  writeFile,
} from 'node:fs/promises';
import path from 'node:path';
import {
  getDocsServerConfig,
  getTelemetryStorageDescription,
  type DocsServerConfig,
} from '@/lib/server/config';
import {
  appendRetainedTelemetryEvents,
  buildTelemetryDashboardSnapshot,
  normalizeTelemetryEvent,
  parseTelemetryStoreData,
  type TelemetryDashboardSnapshot,
  type TelemetryEvent,
  type TelemetryEventInput,
  type TelemetryStoreData,
  type TelemetryWriteResult,
} from '@/lib/server/telemetry-core';

export type {
  TelemetryBackend,
  TelemetryDashboardSnapshot,
  TelemetryEvent,
  TelemetryEventInput,
  TelemetryEventName,
  TelemetryEventSource,
  TelemetryWriteResult,
} from '@/lib/server/telemetry-core';

type TelemetryFileSystem = {
  mkdir(directory: string): Promise<void>;
  readFile(filePath: string): Promise<string>;
  writeFile(filePath: string, content: string): Promise<void>;
  rename(from: string, to: string): Promise<void>;
  unlink(filePath: string): Promise<void>;
};

/** Future Redis bindings must provide atomic batch/retention/cap behavior. */
export type ApprovedRedisTelemetryAdapter = {
  writeBatch(input: {
    events: readonly TelemetryEvent[];
    now: number;
    retentionDays: number;
    maxEvents: number;
  }): Promise<number>;
  readEvents(): Promise<readonly TelemetryEvent[]>;
};

export type TelemetryServiceDependencies = {
  cwd?: string;
  now?: () => number;
  createId?: () => string;
  fileSystem?: TelemetryFileSystem;
  redisAdapter?: ApprovedRedisTelemetryAdapter;
};

export type TelemetryService = {
  recordEvents(
    inputs: readonly TelemetryEventInput[],
  ): Promise<TelemetryWriteResult>;
  getDashboardSnapshot(windowDays: number): Promise<TelemetryDashboardSnapshot>;
};

export class TelemetryStoreUnavailableError extends Error {
  readonly mode: DocsServerConfig['telemetryBackend'];

  constructor(
    mode: DocsServerConfig['telemetryBackend'],
    message = 'Telemetry storage is unavailable.',
  ) {
    super(message);
    this.name = 'TelemetryStoreUnavailableError';
    this.mode = mode;
  }
}

const NODE_FILE_SYSTEM: TelemetryFileSystem = {
  async mkdir(directory) {
    await mkdir(directory, { recursive: true });
  },
  async readFile(filePath) {
    return readFile(filePath, 'utf8');
  },
  async writeFile(filePath, content) {
    await writeFile(filePath, content, {
      encoding: 'utf8',
      flag: 'wx',
      mode: 0o600,
    });
  },
  async rename(from, to) {
    await rename(from, to);
  },
  async unlink(filePath) {
    await unlink(filePath);
  },
};

function hasErrorCode(error: unknown, code: string): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    (error as { code?: unknown }).code === code
  );
}

function redactedSnapshotMetadata(
  config: DocsServerConfig,
  override?: {
    availability: 'available' | 'disabled' | 'unavailable';
    unavailableReason?: 'disabled' | 'configuration' | 'backend';
  },
) {
  const description = getTelemetryStorageDescription(config);
  return {
    adapter: config.telemetryBackend,
    availability: override?.availability ?? description.availability,
    unavailableReason: override?.unavailableReason,
    storageTarget: description.target,
  } as const;
}

export function createTelemetryService(
  config: DocsServerConfig,
  dependencies: TelemetryServiceDependencies = {},
): TelemetryService {
  const fileSystem = dependencies.fileSystem ?? NODE_FILE_SYSTEM;
  const now = dependencies.now ?? Date.now;
  const createId = dependencies.createId ?? (() => crypto.randomUUID());
  const workingDirectory = dependencies.cwd ?? process.cwd();
  const storePath = path.resolve(workingDirectory, config.telemetryStorePath);
  let writeQueue: Promise<void> = Promise.resolve();

  async function readFilesystemStore(): Promise<TelemetryStoreData> {
    let content: string;
    try {
      content = await fileSystem.readFile(storePath);
    } catch (error) {
      if (hasErrorCode(error, 'ENOENT')) {
        return { version: 1, events: [] };
      }
      throw error;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(content);
    } catch (error) {
      throw new TelemetryStoreUnavailableError(
        'filesystem',
        'Telemetry store JSON is invalid.',
      );
    }
    return parseTelemetryStoreData(parsed);
  }

  async function writeFilesystemStore(data: TelemetryStoreData): Promise<void> {
    const directory = path.dirname(storePath);
    const temporaryPath = path.join(
      directory,
      `.${path.basename(storePath)}.${process.pid}.${createId()}.tmp`,
    );
    await fileSystem.mkdir(directory);

    try {
      await fileSystem.writeFile(
        temporaryPath,
        `${JSON.stringify(data, null, 2)}\n`,
      );
      await fileSystem.rename(temporaryPath, storePath);
    } catch (error) {
      try {
        await fileSystem.unlink(temporaryPath);
      } catch {
        // The temporary file may not exist, or cleanup may fail independently.
      }
      throw error;
    }
  }

  function normalizeBatch(
    inputs: readonly TelemetryEventInput[],
    timestamp: number,
  ): TelemetryEvent[] {
    return inputs.map((input) =>
      normalizeTelemetryEvent(input, { now: timestamp, createId }),
    );
  }

  async function recordFilesystemEvents(
    additions: readonly TelemetryEvent[],
    timestamp: number,
  ): Promise<number> {
    let stored = 0;
    const operation = writeQueue.then(async () => {
      const existing = await readFilesystemStore();
      const events = appendRetainedTelemetryEvents({
        existing: existing.events,
        additions,
        now: timestamp,
        retentionDays: config.telemetryRetentionDays,
        maxEvents: config.telemetryMaxEvents,
      });
      const additionIds = new Set(additions.map((event) => event.id));
      stored = events.filter((event) => additionIds.has(event.id)).length;
      await writeFilesystemStore({ version: 1, events });
    });

    // A failed operation rejects its caller but cannot poison later writes.
    writeQueue = operation.then(
      () => undefined,
      () => undefined,
    );
    await operation;
    return stored;
  }

  return {
    async recordEvents(inputs) {
      const timestamp = now();
      const additions = normalizeBatch(inputs, timestamp);

      if (config.telemetryBackend === 'disabled') {
        return {
          mode: 'disabled',
          received: additions.length,
          stored: 0,
        };
      }

      if (config.telemetryBackend === 'redis') {
        if (
          config.telemetryConfigurationIssue ||
          !dependencies.redisAdapter
        ) {
          throw new TelemetryStoreUnavailableError('redis');
        }
        const stored = await dependencies.redisAdapter.writeBatch({
          events: additions,
          now: timestamp,
          retentionDays: config.telemetryRetentionDays,
          maxEvents: config.telemetryMaxEvents,
        });
        return {
          mode: 'redis',
          received: additions.length,
          stored,
        };
      }

      const stored = await recordFilesystemEvents(additions, timestamp);
      return {
        mode: 'filesystem',
        received: additions.length,
        stored,
      };
    },

    async getDashboardSnapshot(windowDays) {
      if (config.telemetryBackend === 'disabled') {
        return buildTelemetryDashboardSnapshot({
          events: [],
          windowDays,
          metadata: redactedSnapshotMetadata(config, {
            availability:
              config.telemetryConfigurationIssue
                ? 'unavailable'
                : 'disabled',
            unavailableReason:
              config.telemetryConfigurationIssue
                ? 'configuration'
                : 'disabled',
          }),
          now: now(),
        });
      }

      if (config.telemetryBackend === 'redis') {
        if (
          config.telemetryConfigurationIssue ||
          !dependencies.redisAdapter
        ) {
          return buildTelemetryDashboardSnapshot({
            events: [],
            windowDays,
            metadata: redactedSnapshotMetadata(config, {
              availability: 'unavailable',
              unavailableReason: config.telemetryConfigurationIssue
                ? 'configuration'
                : 'backend',
            }),
            now: now(),
          });
        }

        try {
          const events = await dependencies.redisAdapter.readEvents();
          return buildTelemetryDashboardSnapshot({
            events: parseTelemetryStoreData({ version: 1, events }).events,
            windowDays,
            metadata: redactedSnapshotMetadata(config, {
              availability: 'available',
            }),
            now: now(),
          });
        } catch {
          return buildTelemetryDashboardSnapshot({
            events: [],
            windowDays,
            metadata: redactedSnapshotMetadata(config, {
              availability: 'unavailable',
              unavailableReason: 'backend',
            }),
            now: now(),
          });
        }
      }

      try {
        const store = await readFilesystemStore();
        return buildTelemetryDashboardSnapshot({
          events: store.events,
          windowDays,
          metadata: redactedSnapshotMetadata(config, {
            availability: 'available',
          }),
          now: now(),
        });
      } catch {
        return buildTelemetryDashboardSnapshot({
          events: [],
          windowDays,
          metadata: redactedSnapshotMetadata(config, {
            availability: 'unavailable',
            unavailableReason: 'backend',
          }),
          now: now(),
        });
      }
    },
  };
}

const defaultService = createTelemetryService(getDocsServerConfig());

export async function recordTelemetryEvents(
  inputs: readonly TelemetryEventInput[],
): Promise<TelemetryWriteResult> {
  return defaultService.recordEvents(inputs);
}

export async function recordTelemetryEvent(
  input: TelemetryEventInput,
): Promise<TelemetryWriteResult> {
  return defaultService.recordEvents([input]);
}

export async function getTelemetryDashboardSnapshot(
  windowDays: number,
): Promise<TelemetryDashboardSnapshot> {
  return defaultService.getDashboardSnapshot(windowDays);
}
