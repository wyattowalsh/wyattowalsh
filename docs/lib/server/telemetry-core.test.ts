import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import type { TelemetryEvent } from './telemetry-core';

type TelemetryCoreModule = typeof import('./telemetry-core');
const {
  appendRetainedTelemetryEvents,
  buildTelemetryDashboardSnapshot,
  isTelemetryEvent,
  normalizeTelemetryEvent,
  parseTelemetryStoreData,
} = (await import(
  new URL('./telemetry-core.ts', import.meta.url).href
)) as TelemetryCoreModule;

const NOW = Date.parse('2026-08-12T12:00:00.000Z');

function event(
  id: string,
  occurredAt: string,
  overrides: Partial<TelemetryEvent> = {},
): TelemetryEvent {
  return {
    id,
    name: 'page_view',
    source: 'server',
    occurredAt,
    pathname: '/docs',
    ...overrides,
  };
}

describe('telemetry core', () => {
  it('normalizes bounded fields and removes referrer query data', () => {
    const metadata = Object.fromEntries(
      Array.from({ length: 25 }, (_, index) => [`key-${index}`, `value-${index}`]),
    );
    const normalized = normalizeTelemetryEvent(
      {
        name: 'page_view',
        source: 'client',
        pathname: ' /docs/getting-started?token=secret#fragment ',
        referrer: 'https://example.com/from?secret=value#fragment',
        href: 'https://outside.example/path?token=secret#fragment',
        method: ' post ',
        statusCode: 999,
        durationMs: -4.4,
        metadata,
      },
      { now: NOW, createId: () => 'event-1' },
    );

    assert.equal(normalized.id, 'event-1');
    assert.equal(normalized.occurredAt, '2026-08-12T12:00:00.000Z');
    assert.equal(normalized.pathname, '/docs/getting-started');
    assert.equal(normalized.referrer, 'https://example.com/from');
    assert.equal(normalized.href, 'https://outside.example/path');
    assert.equal(normalized.method, 'POST');
    assert.equal(normalized.statusCode, undefined);
    assert.equal(normalized.durationMs, 0);
    assert.equal(Object.keys(normalized.metadata ?? {}).length, 20);
  });

  it('rejects invalid runtime event discriminants and timestamps', () => {
    assert.throws(() =>
      normalizeTelemetryEvent({
        name: 'not-an-event' as 'page_view',
        source: 'server',
      }),
    );
    assert.throws(
      () =>
        normalizeTelemetryEvent(
          {
            name: 'page_view',
            source: 'client',
            occurredAt: '2999-01-01T00:00:00.000Z',
          },
          { now: NOW },
        ),
      /future/,
    );
    assert.throws(() =>
      normalizeTelemetryEvent({
        name: 'page_view',
        source: 'server',
        occurredAt: 'not-a-date',
      }),
    );
  });

  it('runtime-validates every persisted event', () => {
    const valid = {
      ...event('valid', '2026-08-12T11:00:00.000Z', {
      pathname: '/docs?secret=value#fragment',
      referrer: 'https://example.com/from?secret=value',
      }),
      password: 'must-not-survive',
      nested: { secret: 'must-not-survive' },
    };
    assert.equal(isTelemetryEvent(valid), true);
    const parsed = parseTelemetryStoreData({ version: 1, events: [valid] });
    assert.equal(parsed.events[0]?.pathname, '/docs');
    assert.equal(parsed.events[0]?.referrer, 'https://example.com/from');
    assert.equal('password' in (parsed.events[0] ?? {}), false);
    assert.equal('nested' in (parsed.events[0] ?? {}), false);
    assert.throws(() =>
      parseTelemetryStoreData({
        version: 1,
        events: [{ ...valid, occurredAt: 'invalid' }],
      }),
    );
    assert.throws(() => parseTelemetryStoreData({ version: 2, events: [] }));
  });

  it('prunes expired events and applies the cap once per batch', () => {
    const retained = appendRetainedTelemetryEvents({
      existing: [
        event('expired', '2026-08-01T12:00:00.000Z'),
        event('existing', '2026-08-12T09:00:00.000Z'),
      ],
      additions: [
        event('expired-addition', '2026-08-01T12:00:00.000Z'),
        event('new-1', '2026-08-12T10:00:00.000Z'),
        event('new-2', '2026-08-12T11:00:00.000Z'),
        event('future-addition', '2999-01-01T00:00:00.000Z'),
      ],
      now: NOW,
      retentionDays: 2,
      maxEvents: 2,
    });

    assert.deepEqual(
      retained.map((item) => item.id),
      ['new-1', 'new-2'],
    );
  });

  it('builds truthful available and disabled snapshots', () => {
    const events = [
      event('view', '2026-08-12T10:00:00.000Z', {
        sessionId: 'session-1',
        referrer: 'https://example.com/from',
      }),
      event('search', '2026-08-12T11:00:00.000Z', {
        name: 'docs_search',
        searchQuery: 'telemetry',
      }),
    ];
    const snapshot = buildTelemetryDashboardSnapshot({
      events,
      windowDays: 1,
      metadata: {
        adapter: 'filesystem',
        availability: 'available',
        storageTarget: 'Local filesystem',
      },
      now: NOW,
    });
    assert.equal(snapshot.summary.pageViews, 1);
    assert.equal(snapshot.summary.searches, 1);
    assert.equal(snapshot.totalRetainedEvents, 2);
    assert.equal(snapshot.storageTarget, 'Local filesystem');

    const disabled = buildTelemetryDashboardSnapshot({
      events: [],
      windowDays: 7,
      metadata: {
        adapter: 'disabled',
        availability: 'disabled',
        unavailableReason: 'disabled',
        storageTarget: 'Custom telemetry disabled',
      },
      now: NOW,
    });
    assert.equal(disabled.totalRetainedEvents, 0);
    assert.equal(disabled.availability, 'disabled');
    assert.equal(disabled.unavailableReason, 'disabled');
  });
});
