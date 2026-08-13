import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import type { TelemetryEventInput } from './telemetry-core';

type ObservationModule = typeof import('./public-telemetry-observation');
const { writeTelemetryObservationsBestEffort } = (await import(
  new URL('./public-telemetry-observation.ts', import.meta.url).href
)) as ObservationModule;

describe('public telemetry observations', () => {
  it('writes all observations as one batch', async () => {
    const expected: TelemetryEventInput[] = [
      { name: 'docs_search', source: 'server', searchQuery: 'config' },
      { name: 'api_request', source: 'server', route: '/api/search' },
    ];
    let received: readonly TelemetryEventInput[] = [];

    await writeTelemetryObservationsBestEffort(
      async (events) => {
        received = events;
        return {
          mode: 'filesystem',
          received: events.length,
          stored: events.length,
        };
      },
      expected,
    );

    assert.deepEqual(received, expected);
  });

  it('absorbs unavailable-store failures', async () => {
    await assert.doesNotReject(
      writeTelemetryObservationsBestEffort(
        async () => {
          throw new Error('store unavailable');
        },
        [{ name: 'api_request', source: 'server' }],
      ),
    );
  });

  it('does not call the writer for an empty batch', async () => {
    let called = false;
    await writeTelemetryObservationsBestEffort(
      async () => {
        called = true;
        return { mode: 'filesystem', received: 0, stored: 0 };
      },
      [],
    );
    assert.equal(called, false);
  });
});
