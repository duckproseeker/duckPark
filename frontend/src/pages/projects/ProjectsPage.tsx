import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { listProjects } from '../../api/projects';
import { listGateways } from '../../api/gateways';
import { listRuns } from '../../api/runs';
import { getSystemStatus } from '../../api/system';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, sortByActivity } from '../../lib/format';
import { deriveBenchmarkSummary, formatMetric, getRunProjectId } from '../../lib/platform';

export function ProjectsPage() {
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const runsQuery = useQuery({ queryKey: ['runs'], queryFn: () => listRuns(), refetchInterval: 5000 });
  const gatewaysQuery = useQuery({ queryKey: ['gateways'], queryFn: listGateways, refetchInterval: 5000 });
  const systemQuery = useQuery({ queryKey: ['system-status'], queryFn: getSystemStatus, refetchInterval: 3000 });

  const projects = projectsQuery.data ?? [];
  const runs = sortByActivity(runsQuery.data ?? []);
  const gateways = sortByActivity(gatewaysQuery.data ?? []);
  const summary = deriveBenchmarkSummary(runs, gateways);
  const activeRuns = runs.filter((run) => ['CREATED', 'QUEUED', 'STARTING', 'RUNNING', 'STOPPING'].includes(run.status)).length;
  const onlineDevices = gateways.filter((gateway) => ['READY', 'BUSY'].includes(gateway.status)).length;
  const latestRuns = runs.slice(0, 5);

  return (
    <div className="page-stack">
      <PageHeader
        title="芯片测评平台"
        eyebrow="Projects / Dashboard"
        chips={['项目总览', '批量测评', '运营看板']}
        description="围绕芯片项目、场景矩阵、批量执行和测评报告组织工作流。首页优先暴露吞吐、延迟、精度、功耗、温度和场景通过率，底层网关与采集链路下沉到设备中心。"
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="horizon-button" to="/executions">
              发起测评任务
            </Link>
            <Link className="horizon-button-secondary" to="/reports">
              查看报告中心
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <MetricCard accent="blue" label="FPS" value={formatMetric(summary.fps, 1)} hint="由 run tick/wall time 与网关 FPS 推导" />
        <MetricCard accent="violet" label="延迟" value={formatMetric(summary.latencyMs, 1, ' ms')} hint="等待 avg_latency_ms 等指标持续回传" />
        <MetricCard accent="teal" label="mAP" value={formatMetric(summary.map, 2)} hint="当前优先读取网关或评测侧回传值" />
        <MetricCard accent="orange" label="功耗" value={formatMetric(summary.powerW, 1, ' W')} hint="未接入时显示待接入" />
        <MetricCard accent="rose" label="温度" value={formatMetric(summary.temperatureC, 1, '°C')} hint="未接入时显示待接入" />
        <MetricCard accent="blue" label="场景通过率" value={formatMetric(summary.passRate, 1, '%')} hint="COMPLETED / 终态 run" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.55fr)_420px]">
        <Panel title="测评项目" subtitle="项目页只呈现业务项目语义，不直接展示具体 DUT 型号。">
          {projects.length === 0 ? (
            <EmptyState title="没有项目目录" description="后端项目模型还没有返回任何数据。" />
          ) : (
            <div className="grid gap-4 xl:grid-cols-3">
              {projects.map((project) => {
                const projectRuns = runs.filter((run) => getRunProjectId(run) === project.project_id);
                const latestRun = projectRuns[0] ?? null;

                return (
                  <div key={project.project_id} className="rounded-[26px] border border-secondaryGray-200 bg-secondaryGray-50/60 p-5 shadow-card">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-[11px] font-extrabold uppercase tracking-[0.18em] text-secondaryGray-500">
                          {project.vendor}
                        </p>
                        <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">
                          {project.name}
                        </strong>
                        <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{project.description}</p>
                      </div>
                      <StatusPill status={project.status} />
                    </div>

                    <div className="mt-5 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                        <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">适用范围</span>
                        <strong className="mt-2 block text-sm text-navy-900">{project.processor}</strong>
                      </div>
                      <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                        <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">已标记执行</span>
                        <strong className="mt-2 block text-sm text-navy-900">{projectRuns.length}</strong>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {project.target_metrics.map((metric) => (
                        <span key={metric} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-secondaryGray-600">
                          {metric}
                        </span>
                      ))}
                    </div>

                    <div className="mt-5 rounded-[20px] border border-white/80 bg-white px-4 py-4">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">最近状态</span>
                      {latestRun ? (
                        <>
                          <div className="mt-3 flex items-center gap-3">
                            <StatusPill status={latestRun.status} />
                            <span className="text-sm font-bold text-brand-600">{project.name}</span>
                          </div>
                          <p className="mt-3 text-sm text-secondaryGray-600">
                            {latestRun.scenario_name} / {latestRun.map_name}
                          </p>
                          <p className="mt-1 text-xs text-secondaryGray-500">{formatDateTime(latestRun.updated_at_utc)}</p>
                        </>
                      ) : (
                        <p className="mt-3 text-sm leading-6 text-secondaryGray-600">
                          当前项目还没有写入 `project:{project.project_id}` 标签的执行记录。执行中心新建测评任务后会自动附带项目标签。
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel title="平台运行态" subtitle="把执行器、设备和报告入口放在一起，避免首页沦为运维面板。">
            <div className="grid gap-3">
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">执行器状态</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">
                  {systemQuery.data?.executor.status ?? 'UNKNOWN'}
                </strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">运行中执行</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{activeRuns}</strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">在线设备</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{onlineDevices}</strong>
              </div>
            </div>
          </Panel>

          <Panel title="最近执行" subtitle="首页只保留业务上最需要追踪的最近执行摘要。">
            {latestRuns.length === 0 ? (
              <EmptyState title="暂无执行记录" description="去执行中心创建第一批测评任务，平台就会开始沉淀项目级数据。" />
            ) : (
              <div className="flex flex-col gap-3">
                {latestRuns.map((run) => (
                  <Link
                    key={run.run_id}
                    className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4 transition hover:-translate-y-0.5 hover:shadow-card"
                    to={`/executions/${run.run_id}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <strong className="block truncate text-sm font-bold text-navy-900">
                          {run.scenario_name} / {run.map_name}
                        </strong>
                        <p className="mt-1 truncate text-xs text-secondaryGray-500">{run.run_id}</p>
                      </div>
                      <StatusPill status={run.status} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
