import { apiRequest, postJson } from './client';
import type { CreateRunPayload, RunEnvironmentState, RunEvent, RunRecord, RunViewerInfo, WeatherConfig } from './types';

export function listRuns(status?: string) {
  return apiRequest<RunRecord[]>('/runs', {
    query: { status }
  });
}

export function getRun(runId: string) {
  return apiRequest<RunRecord>(`/runs/${runId}`);
}

export function getRunEvents(runId: string) {
  return apiRequest<RunEvent[]>(`/runs/${runId}/events`);
}

export function createRun(payload: CreateRunPayload) {
  return postJson<{ run_id: string; status: string }>('/runs', payload);
}

export function startRun(runId: string) {
  return postJson<RunRecord>(`/runs/${runId}/start`);
}

export function stopRun(runId: string) {
  return postJson<RunRecord>(`/runs/${runId}/stop`);
}

export function cancelRun(runId: string) {
  return postJson<RunRecord>(`/runs/${runId}/cancel`);
}

export function getRunEnvironment(runId: string) {
  return apiRequest<RunEnvironmentState>(`/runs/${runId}/environment`);
}

export function updateRunEnvironment(
  runId: string,
  payload: {
    weather: WeatherConfig;
    debug?: {
      viewer_friendly?: boolean;
    };
  }
) {
  return postJson<RunEnvironmentState>(`/runs/${runId}/environment`, payload);
}

export function getRunViewer(runId: string) {
  return apiRequest<RunViewerInfo>(`/runs/${runId}/viewer`);
}
