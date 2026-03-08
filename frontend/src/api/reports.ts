import { apiRequest, postJson } from './client';
import type { ReportRecord } from './types';

export function listReports(filters: { benchmarkTaskId?: string } = {}) {
  return apiRequest<{ reports: ReportRecord[] }>('/reports', {
    query: {
      benchmark_task_id: filters.benchmarkTaskId
    }
  }).then((data) => data.reports);
}

export function getReport(reportId: string) {
  return apiRequest<ReportRecord>(`/reports/${reportId}`);
}

export function exportReport(benchmarkTaskId: string) {
  return postJson<ReportRecord>('/reports/export', { benchmark_task_id: benchmarkTaskId });
}
