import { useEffect, useMemo, useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { exportReport, getReportsWorkspace } from '../../api/reports';
import { CompactPageHeader } from '../../components/common/CompactPageHeader';
import { DetailPanel } from '../../components/common/DetailPanel';
import { EmptyState } from '../../components/common/EmptyState';
import { SelectionList } from '../../components/common/SelectionList';
import { StatusPanel } from '../../components/common/StatusPanel';
import { formatDateTime } from '../../lib/format';

export function ReportsPage() {
  const queryClient = useQueryClient();
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);

  const workspaceQuery = useQuery({
    queryKey: ['reports', 'workspace'],
    queryFn: getReportsWorkspace,
    refetchInterval: 5000
  });

  const workspace = workspaceQuery.data;
  const reports = workspace?.reports ?? [];
  const benchmarkTasks = workspace?.benchmark_tasks ?? [];
  const recentFailures = workspace?.recent_failures ?? [];
  const exportableTasks = workspace?.exportable_tasks ?? [];
  const pendingReportTasks = workspace?.pending_report_tasks ?? [];
  const selectedReport = reports.find((item) => item.report_id === selectedReportId) ?? reports[0] ?? null;
  const selectedTask = selectedReport
    ? benchmarkTasks.find((item) => item.benchmark_task_id === selectedReport.benchmark_task_id) ?? null
    : null;

  useEffect(() => {
    if (selectedReport && selectedReport.report_id !== selectedReportId) {
      setSelectedReportId(selectedReport.report_id);
    }
  }, [selectedReport, selectedReportId]);

  const comparisonRows = useMemo(() => {
    if (!selectedTask) {
      return [];
    }
    return [
      { label: 'Total Runs', value: selectedTask.summary.counts?.total_runs ?? '-' },
      { label: 'Completed', value: selectedTask.summary.counts?.completed_runs ?? '-' },
      { label: 'Failed', value: selectedTask.summary.counts?.failed_runs ?? '-' },
      { label: 'Canceled', value: selectedTask.summary.counts?.canceled_runs ?? '-' },
      { label: 'Running', value: selectedTask.summary.counts?.running_runs ?? '-' }
    ];
  }, [selectedTask]);

  const exportMutation = useMutation({
    mutationFn: (benchmarkTaskId: string) => exportReport(benchmarkTaskId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['reports'] });
    }
  });

  const latestExportableTask = exportableTasks[0] ?? null;
  const selectedMetrics = selectedReport?.summary.metrics ?? selectedTask?.summary.metrics ?? null;

  return (
    <div className="page-stack">
      <CompactPageHeader
        stepLabel="Step 5 / Reports"
        title="报告分析工作台"
        description="报告中心聚焦分析和导出。左侧报告列表，中间摘要与对比，右侧给出导出动作和异常结论。"
        contextSummary={selectedReport ? `当前报告 ${selectedReport.title}` : '暂无报告资产'}
        actions={
          <>
            {latestExportableTask && (
              <button
                className="horizon-button"
                disabled={exportMutation.isPending}
                onClick={() => exportMutation.mutate(latestExportableTask.benchmark_task_id)}
                type="button"
              >
                {exportMutation.isPending ? '导出中...' : '导出最新任务报告'}
              </button>
            )}
            <Link className="horizon-button-secondary" to="/executions" viewTransition>
              返回执行中心
            </Link>
          </>
        }
      />

      <div className="grid gap-3 xl:grid-cols-[320px_minmax(0,1fr)_320px]">
        <DetailPanel subtitle="按报告资产浏览历史结果" title="报告列表">
          {workspaceQuery.isLoading ? (
            <EmptyState description="正在同步报告归档与导出队列。" title="报告工作台加载中" />
          ) : workspaceQuery.isError ? (
            <EmptyState
              description={workspaceQuery.error instanceof Error ? workspaceQuery.error.message : '报告工作台接口异常。'}
              title="报告工作台加载失败"
            />
          ) : (
            <SelectionList
              emptyDescription="执行完成后导出报告会出现在这里。"
              emptyTitle="暂无报告"
              items={reports.map((report) => ({
                id: report.report_id,
                title: report.title,
                subtitle: `Task ${report.benchmark_task_id}`,
                meta: formatDateTime(report.updated_at_utc),
                status: report.status,
                hint: report.dut_model ?? 'No DUT'
              }))}
              onSelect={setSelectedReportId}
              selectedId={selectedReport?.report_id ?? null}
            />
          )}
        </DetailPanel>

        <div className="grid gap-3">
          <DetailPanel subtitle="当前报告摘要" title="报告主视图">
            {!selectedReport ? (
              <EmptyState description="左侧选择一个报告查看摘要。" title="未选择报告" />
            ) : (
              <div className="grid gap-3">
                <div className="workbench-surface">
                  <h3 className="workbench-surface__title">{selectedReport.title}</h3>
                  <p className="workbench-copy" style={{ marginTop: '0.45rem' }}>
                    Report ID: {selectedReport.report_id}
                  </p>
                  <p className="workbench-copy">
                    Project: {selectedReport.project_id} / Benchmark: {selectedReport.benchmark_definition_id}
                  </p>
                  <p className="workbench-copy">DUT: {selectedReport.dut_model ?? '未登记'}</p>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="workbench-surface">
                    <p className="workbench-kicker">运行对比摘要</p>
                    {comparisonRows.length === 0 ? (
                      <p className="workbench-copy" style={{ marginTop: '0.45rem' }}>
                        缺少关联 task summary。
                      </p>
                    ) : (
                      <div className="workbench-stack" style={{ marginTop: '0.45rem' }}>
                        {comparisonRows.map((row) => (
                          <p className="workbench-copy" key={row.label}>
                            {row.label}: {row.value}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="workbench-surface">
                    <p className="workbench-kicker">平台聚合指标</p>
                    <p className="workbench-copy" style={{ marginTop: '0.45rem' }}>
                      FPS: {selectedMetrics?.fps?.toFixed(1) ?? 'Pending'}
                    </p>
                    <p className="workbench-copy">
                      Pass Rate: {selectedMetrics?.pass_rate?.toFixed(1) ?? 'Pending'}%
                    </p>
                    <p className="workbench-copy">
                      Anomaly Rate: {selectedMetrics?.anomaly_rate?.toFixed(1) ?? 'Pending'}%
                    </p>
                  </div>
                </div>

                <div className="workbench-surface">
                  <p className="workbench-kicker">下载与导出</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <a
                      className="horizon-button-secondary"
                      href={`/reports/${selectedReport.report_id}/download?format=json`}
                      rel="noreferrer"
                      target="_blank"
                    >
                      下载 JSON
                    </a>
                    <a
                      className="horizon-button-secondary"
                      href={`/reports/${selectedReport.report_id}/download?format=markdown`}
                      rel="noreferrer"
                      target="_blank"
                    >
                      下载 Markdown
                    </a>
                  </div>
                </div>
              </div>
            )}
          </DetailPanel>

          <DetailPanel subtitle="失败和取消优先复盘" title="异常对比">
            <SelectionList
              emptyDescription="当前没有失败或取消的执行。"
              emptyTitle="无异常执行"
              items={recentFailures.map((run) => ({
                id: run.run_id,
                title: run.scenario_name,
                subtitle: run.error_reason ?? run.map_name,
                meta: formatDateTime(run.updated_at_utc),
                status: run.status,
                hint: run.run_id
              }))}
              onSelect={() => undefined}
              selectedId={null}
            />
          </DetailPanel>
        </div>

        <div className="flex flex-col gap-3">
          <StatusPanel
            label="Report Coverage"
            note={`${workspace?.summary.report_count ?? 0} reports / ${workspace?.summary.benchmark_task_count ?? 0} benchmark tasks`}
            status={reports.length > 0 ? 'READY' : 'UNKNOWN'}
          />
          <StatusPanel
            label="Export Queue"
            note={`${workspace?.summary.exportable_task_count ?? 0} tasks can be exported`}
            status={exportableTasks.length > 0 ? 'READY' : 'UNKNOWN'}
          />
          <StatusPanel
            label="Failure Focus"
            note={`${workspace?.summary.recent_failure_count ?? 0} recent failed or canceled runs`}
            status={recentFailures.length > 0 ? 'FAILED' : 'COMPLETED'}
          />

          <DetailPanel subtitle="这些任务已经具备报告条件，但还没有归档资产" title="待补归档">
            {pendingReportTasks.length === 0 ? (
              <EmptyState description="当前没有待补归档的任务。" title="归档已同步" />
            ) : (
              <div className="workbench-stack">
                {pendingReportTasks.slice(0, 4).map((task) => (
                  <p className="workbench-copy" key={task.benchmark_task_id}>
                    {task.benchmark_name} / {task.dut_model ?? '未登记 DUT'} / {task.status}
                  </p>
                ))}
              </div>
            )}
          </DetailPanel>
        </div>
      </div>
    </div>
  );
}
