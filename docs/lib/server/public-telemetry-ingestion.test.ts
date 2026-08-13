import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

type IngestionModule = typeof import('./public-telemetry-ingestion');
const {
  handlePublicTelemetryIngestion,
  parseClientTelemetryPayload,
} = (await import(
  new URL('./public-telemetry-ingestion.ts', import.meta.url).href
)) as IngestionModule;

function request(body: string): Request {
  return new Request('https://docs.example/api/telemetry/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  });
}

describe('public telemetry ingestion', () => {
  it('accepts only bounded client event fields', () => {
    const parsed = parseClientTelemetryPayload({
      events: [
        {
          name: 'page_view',
          source: 'server',
          pathname: '/docs/0',
          label: 'CTA 0',
          metadata: { secret: 'discarded' },
        },
      ],
    });

    assert.equal(parsed.length, 1);
    assert.equal(parsed[0]?.source, 'client');
    assert.equal(parsed[0]?.pathname, '/docs/0');
    assert.equal(parsed[0]?.metadata, undefined);
  });

  it('rejects oversized batches instead of silently dropping events', () => {
    const events = Array.from({ length: 25 }, (_, index) => ({
      name: index % 2 === 0 ? 'page_view' : 'cta_click',
      source: 'server',
      pathname: `/docs/${index}`,
      label: `CTA ${index}`,
      metadata: { secret: 'discarded' },
    }));

    assert.throws(
      () => parseClientTelemetryPayload({ events }),
      /more than 20 events/,
    );
  });

  it('rejects oversized bodies and future client timestamps', async () => {
    assert.throws(
      () =>
        parseClientTelemetryPayload(
          {
            events: [
              { name: 'page_view', occurredAt: '2999-01-01T00:00:00.000Z' },
            ],
          },
          { now: Date.parse('2026-08-12T12:00:00.000Z') },
        ),
      /timestamp/,
    );

    const response = await handlePublicTelemetryIngestion(
      request(JSON.stringify({ events: [], padding: 'x'.repeat(33 * 1024) })),
      {
        async recordEvents(events) {
          return { mode: 'filesystem', received: events.length, stored: 0 };
        },
      },
    );
    assert.equal(response.status, 400);
  });

  it('rejects malformed payloads and unsupported client event names', () => {
    assert.throws(() => parseClientTelemetryPayload({}), /events array/);
    assert.throws(
      () => parseClientTelemetryPayload({ events: [{ name: 'api_error' }] }),
      /not accepted/,
    );
    assert.throws(
      () =>
        parseClientTelemetryPayload({
          events: [{ name: 'page_view', pathname: 42 }],
        }),
      /must be a string/,
    );
  });

  it('returns truthful batch results, including disabled mode', async () => {
    const response = await handlePublicTelemetryIngestion(
      request(
        JSON.stringify({
          events: [{ name: 'page_view', pathname: '/docs' }],
        }),
      ),
      {
        async recordEvents(events) {
          return { mode: 'disabled', received: events.length, stored: 0 };
        },
      },
    );

    assert.equal(response.status, 202);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.deepEqual(await response.json(), {
      ok: true,
      mode: 'disabled',
      received: 1,
      stored: 0,
    });
  });

  it('returns 400 for invalid JSON without calling storage', async () => {
    let called = false;
    const response = await handlePublicTelemetryIngestion(request('{'), {
      async recordEvents() {
        called = true;
        return { mode: 'filesystem', received: 0, stored: 0 };
      },
    });

    assert.equal(response.status, 400);
    assert.equal(called, false);
  });

  it('returns 503 when the configured backend cannot store the batch', async () => {
    const response = await handlePublicTelemetryIngestion(
      request(JSON.stringify({ events: [] })),
      {
        async recordEvents() {
          throw new Error('backend unavailable');
        },
      },
    );

    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), {
      ok: false,
      error: 'Telemetry storage is unavailable.',
    });
  });
});
