import { handlePublicTelemetryIngestion } from '@/lib/server/public-telemetry-ingestion';
import { recordTelemetryEvents } from '@/lib/server/telemetry-store';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  return handlePublicTelemetryIngestion(request, {
    recordEvents: recordTelemetryEvents,
  });
}
