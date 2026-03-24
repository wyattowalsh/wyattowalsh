import { source } from '@/lib/source';
import { createSearchAPI } from 'fumadocs-core/search/server';
import { getRequestId, recordApiObservation } from '@/lib/server/telemetry';
import { recordTelemetryEvent } from '@/lib/server/telemetry-store';

const { GET: handleSearch } = createSearchAPI('simple', {
  indexes: source.getPages().map((page) => ({
    title: page.data.title,
    description: page.data.description,
    url: page.url,
    content: page.data.description ?? '',
  })),
});

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const startedAt = performance.now();
  const requestId = getRequestId(request);

  try {
    const response = await handleSearch(request);
    const url = new URL(request.url);
    const searchQuery = url.searchParams.get('query') ?? url.searchParams.get('q');

    if (searchQuery) {
      await recordTelemetryEvent({
        name: 'docs_search',
        source: 'server',
        pathname: '/docs',
        route: '/api/search',
        method: 'GET',
        searchQuery,
        statusCode: response.status,
        durationMs: performance.now() - startedAt,
        requestId,
        outcome: response.ok ? 'success' : 'error',
      });
    }

    await recordApiObservation({
      route: '/api/search',
      method: 'GET',
      statusCode: response.status,
      durationMs: performance.now() - startedAt,
      requestId,
      errorMessage: response.ok ? undefined : 'Search request failed.',
    });

    return response;
  } catch (error) {
    await recordApiObservation({
      route: '/api/search',
      method: 'GET',
      statusCode: 500,
      durationMs: performance.now() - startedAt,
      requestId,
      errorMessage:
        error instanceof Error ? error.message : 'Unknown docs search failure.',
    });

    throw error;
  }
}
