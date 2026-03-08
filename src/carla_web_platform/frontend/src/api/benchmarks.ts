import { apiRequest, postJson } from './client';
import type { BenchmarkDefinition, BenchmarkTaskRecord, CreateBenchmarkTaskPayload } from './types';

export function listBenchmarkDefinitions() {
  return apiRequest<{ definitions: BenchmarkDefinition[] }>('/benchmark-definitions').then((data) => data.definitions);
}

export function listBenchmarkTasks(filters: { projectId?: string; status?: string } = {}) {
  return apiRequest<{ tasks: BenchmarkTaskRecord[] }>('/benchmark-tasks', {
    query: {
      project_id: filters.projectId,
      status: filters.status
    }
  }).then((data) => data.tasks);
}

export function getBenchmarkTask(benchmarkTaskId: string) {
  return apiRequest<BenchmarkTaskRecord>(`/benchmark-tasks/${benchmarkTaskId}`);
}

export function createBenchmarkTask(payload: CreateBenchmarkTaskPayload) {
  return postJson<BenchmarkTaskRecord>('/benchmark-tasks', payload);
}
