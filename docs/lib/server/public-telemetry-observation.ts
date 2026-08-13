import type {
  TelemetryEventInput,
  TelemetryWriteResult,
} from './telemetry-core';

export type TelemetryBatchWriter = (
  events: readonly TelemetryEventInput[],
) => Promise<TelemetryWriteResult>;

/**
 * Persist non-critical observations without allowing telemetry failures to
 * change the primary request's result.
 */
export async function writeTelemetryObservationsBestEffort(
  writer: TelemetryBatchWriter,
  events: readonly TelemetryEventInput[],
): Promise<void> {
  if (events.length === 0) {
    return;
  }

  try {
    await writer(events);
  } catch {
    // Observation telemetry must never mask or replace the primary response.
  }
}
