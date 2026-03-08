import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { listBenchmarkTasks } from '../../api/benchmarks';
import { listCaptures } from '../../api/captures';
import { listGateways } from '../../api/gateways';
import { listProjects } from '../../api/projects';
import { exportReport, listReports } from '../../api/reports';
import { listRuns } from '../../api/runs';
import { DonutStatusChart } from '../../components/common/DonutStatusChart';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, sortByActivity } from '../../lib/format';
import { deriveBenchmarkSummary, formatMetric } from '../../lib/platform';

function chartColorForStatus(status: string) {
  if (status === 'COMPLETED' || status === 'READY') {
    return '#01B574';
  }
  if (status === 'FAILED' || status === 'ERROR' || status === 'CANCELED') {
    return '#EE5D50';
  }
  if (status === 'RUNNING' || status === 'STARTING' || status === 'QUEUED' || status === 'STOPPING' || status === 'BUSY') {
    return '#FFB547';
  }
  return '#A3AED0';
}

export function ReportsPage() {
  const queryClient = useQueryClient();
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const benchmarkTasksQuery = useQuery({ queryKey: ['benchmark-tasks'], queryFn: () => listBenchmarkTasks(), refetchInterval: 5000 });
  const reportsQuery = useQuery({ queryKey: ['reports'], queryFn: () => listReports(), refetchInterval: 5000 });
  const runsQuery = useQuery({ queryKey: ['runs'], queryFn: () => listRuns(), refetchInterval: 5000 });
  const gatewaysQuery = useQuery({ queryKey: ['gateways'], queryFn: listGateways, refetchInterval: 5000 });
  const capturesQuery = useQuery({ queryKey: ['captures'], queryFn: () => listCaptures(), refetchInterval: 5000 });

  const runs = sortByActivity(runsQuery.data ?? []);
  const gateways = sortByActivity(gatewaysQuery.data ?? []);
  const captures = sortByActivity(capturesQuery.data ?? []);
  const activeProjectIds = new Set((projectsQuery.data ?? []).map((item) => item.project_id));
  const benchmarkTasks = (benchmarkTasksQuery.data ?? []).filter((task) => activeProjectIds.has(task.project_id));
  const reports = (reportsQuery.data ?? []).filter((report) => activeProjectIds.has(report.project_id));
  const summary = deriveBenchmarkSummary(runs, gateways);
  const recentFailures = runs.filter((run) => ['FAILED', 'CANCELED'].includes(run.status)).slice(0, 5);
  const latestExportableTask =
    benchmarkTasks.find((task) => ['COMPLETED', 'PARTIAL_FAILED', 'FAILED', 'CANCELED'].includes(task.status)) ?? null;

  const exportMutation = useMutation({
    mutationFn: (benchmarkTaskId: string) => exportReport(benchmarkTaskId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['reports'] });
    }
  });

  const runCounts = runs.reduce<Record<string, number>>((accumulator, run) => {
    accumulator[run.status] = (accumulator[run.status] ?? 0) + 1;
    return accumulator;
  }, {});

  const gatewayCounts = gateways.reduce<Record<string, number>>((accumulator, gateway) => {
    accumulator[gateway.status] = (accumulator[gateway.status] ?? 0) + 1;
    return accumulator;
  }, {});

  const captureCounts = captures.reduce<Record<string, number>>((accumulator, capture) => {
    accumulator[capture.status] = (accumulator[capture.status] ?? 0) + 1;
    return accumulator;
  }, {});

  return (
    <div className="page-stack">
      <PageHeader
        title="报告中心"
        eyebrow="Reports / Dashboard"
        chips={['运营总览', '工程分析', '导出预留']}
        description="报告中心承接两个视角：一是运营看板式总览，二是工程分析式复盘。现在已补上后端报告模型，导出动作会把基准任务沉淀成可追踪的 JSON / Markdown 报告资产。"
        actions={
          <div className="flex flex-wrap gap-3">
            {latestExportableTask && (
              <button className="horizon-button" disabled={exportMutation.isPending} onClick={() => exportMutation.mutate(latestExportableTask.benchmark_task_id)} type="button">
                {exportMutation.isPending ? '导出中...' : '导出最新任务报告'}
              </button>
            )}
            <Link className="horizon-button-secondary" to="/executions">
              返回执行中心
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <MetricCard accent="blue" label="FPS" value={formatMetric(summary.fps, 1)} hint="执行侧吞吐" />
        <MetricCard accent="violet" label="延迟" value={formatMetric(summary.latencyMs, 1, ' ms')} hint="平均延迟" />
        <MetricCard accent="teal" label="mAP" value={formatMetric(summary.map, 2)} hint="模型精度" />
        <MetricCard accent="orange" label="功耗" value={formatMetric(summary.powerW, 1, ' W')} hint="待真实回传" />
        <MetricCard accent="rose" label="温度" value={formatMetric(summary.temperatureC, 1, '°C')} hint="待真实回传" />
        <MetricCard accent="blue" label="场景通过率" value={formatMetric(summary.passRate, 1, '%')} hint="已结束执行的完成率" />
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Panel>
          <DonutStatusChart
            title="执行状态"
            subtitle="用于看当前测评任务是否健康闭环。"
            items={Object.entries(runCounts).map(([label, value]) => ({
              label,
              value,
              color: chartColorForStatus(label)
            }))}
          />
        </Panel>

        <Panel>
          <DonutStatusChart
            title="设备状态"
            subtitle="设备中心异常会直接影响测评闭环。"
            items={Object.entries(gatewayCounts).map(([label, value]) => ({
              label,
              value,
              color: chartColorForStatus(label)
            }))}
          />
        </Panel>

        <Panel>
          <DonutStatusChart
            title="采集状态"
            subtitle="用于确认采集链路是否有落盘证据。"
            items={Object.entries(captureCounts).map(([label, value]) => ({
              label,
              value,
              color: chartColorForStatus(label)
            }))}
          />
        </Panel>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_420px]">
        <Panel title="最近异常" subtitle="工程分析先从失败和取消的执行开始。">
          {recentFailures.length === 0 ? (
            <EmptyState title="暂无异常执行" description="当前没有 FAILED / CANCELED 的执行记录。" />
          ) : (
            <div className="flex flex-col gap-4">
              {recentFailures.map((run) => (
                <Link
                  key={run.run_id}
                  className="rounded-[22px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4 transition hover:-translate-y-0.5 hover:shadow-card"
                  to={`/executions/${run.run_id}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <strong className="block truncate text-sm font-bold text-navy-900">
                        {run.scenario_name} / {run.map_name}
                      </strong>
                      <p className="mt-1 truncate text-xs text-secondaryGray-500">{run.error_reason ?? '无错误说明'}</p>
                      <p className="mt-1 text-xs text-secondaryGray-500">{formatDateTime(run.updated_at_utc)}</p>
                    </div>
                    <StatusPill status={run.status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel title="已导出报告" subtitle="这里直接读取后端 report 模型，而不是靠页面临时拼接。">
            {reports.length === 0 ? (
              <EmptyState title="暂无导出报告" description="先在执行中心跑完一批任务，再从这里导出报告。" />
            ) : (
              <div className="flex flex-col gap-3">
                {reports.slice(0, 6).map((report) => (
                  <div key={report.report_id} className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <strong className="block truncate text-sm font-bold text-navy-900">{report.title}</strong>
                        <p className="mt-1 truncate text-xs text-secondaryGray-500">{report.report_id}</p>
                        <p className="mt-1 truncate text-xs text-secondaryGray-500">DUT: {report.dut_model ?? '未登记'}</p>
                        <p className="mt-1 text-xs text-secondaryGray-500">{formatDateTime(report.updated_at_utc)}</p>
                      </div>
                      <StatusPill status={report.status} />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <a className="horizon-button-secondary" href={`/reports/${report.report_id}/download?format=json`} target="_blank" rel="noreferrer">
                        JSON
                      </a>
                      <a className="horizon-button-secondary" href={`/reports/${report.report_id}/download?format=markdown`} target="_blank" rel="noreferrer">
                        Markdown
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="指标说明">
            <div className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4 text-sm leading-6 text-secondaryGray-600">
              <p>1. FPS 优先使用 run tick / wall time 与设备 FPS 指标推导。</p>
              <p>2. 延迟、mAP、功耗、温度如果没有后端数据源，会明确显示待接入。</p>
              <p>3. 导出报告来自后端 benchmark task + report 模型，不再依赖页面即时拼接。</p>
              <p>4. 运营看板看总览，工程分析请从执行详情和设备详情下钻。</p>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
