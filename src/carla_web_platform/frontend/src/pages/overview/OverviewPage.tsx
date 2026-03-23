import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { listCaptures } from '../../api/captures';
import { listGateways } from '../../api/gateways';
import { listRuns } from '../../api/runs';
import { getSystemStatus } from '../../api/system';
import { DonutStatusChart } from '../../components/common/DonutStatusChart';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, sortByActivity } from '../../lib/format';

function chartColorForStatus(status: string) {
  if (status === 'COMPLETED' || status === 'READY') {
    return '#01B574';
  }
  if (status === 'DEGRADED') {
    return '#FFB547';
  }
  if (status === 'FAILED' || status === 'ERROR' || status === 'CANCELED') {
    return '#EE5D50';
  }
  if (status === 'RUNNING' || status === 'STARTING' || status === 'QUEUED' || status === 'STOPPING' || status === 'BUSY') {
    return '#FFB547';
  }
  return '#A3AED0';
}

export function OverviewPage() {
  const queryClient = useQueryClient();
  const runsQuery = useQuery({ queryKey: ['runs'], queryFn: () => listRuns(), refetchInterval: 5000 });
  const gatewaysQuery = useQuery({
    queryKey: ['gateways'],
    queryFn: listGateways,
    refetchInterval: 5000
  });
  const capturesQuery = useQuery({
    queryKey: ['captures'],
    queryFn: () => listCaptures(),
    refetchInterval: 5000
  });
  const systemQuery = useQuery({
    queryKey: ['system-status'],
    queryFn: getSystemStatus,
    refetchInterval: 3000
  });

  const runs = sortByActivity(runsQuery.data ?? []);
  const gateways = sortByActivity(gatewaysQuery.data ?? []);
  const captures = sortByActivity(capturesQuery.data ?? []);
  const activeRuns = runs.filter((item) => ['CREATED', 'QUEUED', 'STARTING', 'RUNNING', 'STOPPING'].includes(item.status));
  const onlineGateways = gateways.filter((item) => ['READY', 'BUSY', 'DEGRADED'].includes(item.status));
  const activeCaptures = captures.filter((item) => item.status === 'RUNNING');
  const completedCaptures = captures.filter((item) => item.status === 'COMPLETED').length;
  const systemStatus = systemQuery.data;
  const latestCapture = captures[0];
  const latestGateway = gateways[0];
  const recentFailures = [
    ...runs.filter((item) => item.status === 'FAILED').map((item) => ({
      id: item.run_id,
      type: 'Run',
      status: item.status,
      message: item.error_reason ?? '运行失败'
    })),
    ...captures.filter((item) => item.status === 'FAILED').map((item) => ({
      id: item.capture_id,
      type: 'Capture',
      status: item.status,
      message: item.error_reason ?? '采集失败'
    })),
    ...gateways
      .filter((item) => item.status === 'ERROR')
      .map((item) => ({
        id: item.gateway_id,
        type: 'Gateway',
        status: item.status,
        message: String(item.metrics.last_error ?? '网关进入错误状态')
      }))
  ].slice(0, 6);

  const refreshAll = () => {
    void queryClient.invalidateQueries();
  };

  return (
    <div className="page-stack">
      <PageHeader
        title="Overview"
        description="控制面总览。先关注运行、网关和采集的活跃状态，再进入详情页处理异常。"
        actions={
          <div className="flex flex-wrap gap-3">
            <button className="horizon-button-secondary" onClick={refreshAll} type="button">
              刷新总览
            </button>
            <Link className="horizon-button" to="/studio">
              打开 Studio
            </Link>
            <Link className="horizon-button" to="/captures">
              新建采集
            </Link>
          </div>
        }
      />

      {systemStatus?.executor.alive === false && systemStatus.executor.pending_commands > 0 && (
        <div className="rounded-[20px] border border-rose-100 bg-rose-50/90 px-5 py-4">
          <strong>Executor 当前不在线。</strong>
          <span className="mt-1 block text-sm text-rose-600">
            队列里还有 {systemStatus.executor.pending_commands} 条待执行命令，所以新建 run 会停在 QUEUED。
          </span>
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.55fr)_360px]">
        <div className="horizon-card bg-hero-grid overflow-hidden rounded-[32px] border border-white/90 bg-white/95 px-6 py-6 md:px-7 md:py-7">
          <div className="flex flex-col gap-8 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0">
              <span
                className={
                  systemStatus?.executor.alive
                    ? 'inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-extrabold uppercase tracking-[0.16em] text-emerald-600'
                    : 'inline-flex rounded-full bg-amber-50 px-3 py-1 text-xs font-extrabold uppercase tracking-[0.16em] text-amber-600'
                }
              >
                {systemStatus?.executor.alive ? 'Executor linked' : 'Executor unavailable'}
              </span>
              <h2 className="mt-5 max-w-3xl text-3xl font-extrabold tracking-[-0.05em] text-navy-900 md:text-[40px]">
                {systemStatus?.executor.alive ? 'Scenario dispatch and capture orchestration are online' : 'Runs remain queued until the executor service recovers'}
              </h2>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-secondaryGray-600 md:text-base">
                API {systemStatus?.api.status ?? 'loading'} / Queue {systemStatus?.executor.pending_commands ?? 0} / Latest capture{' '}
                {systemStatus?.capture_observability.latest_capture_id ?? '-'}
              </p>
            </div>

            <div className="grid min-w-[260px] gap-3 sm:grid-cols-3 xl:grid-cols-1">
              <div className="rounded-[24px] border border-secondaryGray-200 bg-white/90 px-4 py-4 shadow-card">
                <span className="block text-[11px] font-extrabold uppercase tracking-[0.18em] text-secondaryGray-500">Pending</span>
                <strong className="mt-3 block text-3xl font-extrabold tracking-[-0.04em] text-navy-900">
                  {systemStatus?.executor.pending_commands ?? 0}
                </strong>
              </div>
              <div className="rounded-[24px] border border-secondaryGray-200 bg-white/90 px-4 py-4 shadow-card">
                <span className="block text-[11px] font-extrabold uppercase tracking-[0.18em] text-secondaryGray-500">Online GW</span>
                <strong className="mt-3 block text-3xl font-extrabold tracking-[-0.04em] text-navy-900">{onlineGateways.length}</strong>
              </div>
              <div className="rounded-[24px] border border-secondaryGray-200 bg-white/90 px-4 py-4 shadow-card">
                <span className="block text-[11px] font-extrabold uppercase tracking-[0.18em] text-secondaryGray-500">Completed Capture</span>
                <strong className="mt-3 block text-3xl font-extrabold tracking-[-0.04em] text-navy-900">{completedCaptures}</strong>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4">
          <Panel>
            <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-secondaryGray-500">Latest Capture</p>
            <strong className="mt-3 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{latestCapture?.capture_id ?? '-'}</strong>
            <p className="mt-2 text-sm leading-6 text-secondaryGray-600">
              {latestCapture ? `${latestCapture.saved_frames} frames via ${latestCapture.gateway_id}` : '没有采集记录'}
            </p>
          </Panel>

          <Panel>
            <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-secondaryGray-500">Gateway Feed</p>
            <strong className="mt-3 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{latestGateway?.name ?? 'No gateway'}</strong>
            <p className="mt-2 text-sm leading-6 text-secondaryGray-600">
              {latestGateway ? String(latestGateway.metrics.capture_resolution ?? latestGateway.address ?? '-') : '等待 agent 心跳'}
            </p>
          </Panel>

          <Panel className="bg-rose-50/70">
            <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-rose-500">Recent Failures</p>
            <strong className="mt-3 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{recentFailures.length}</strong>
            <p className="mt-2 text-sm leading-6 text-secondaryGray-600">
              {recentFailures.length > 0 ? recentFailures[0].message : '当前没有 FAILED / ERROR 项'}
            </p>
          </Panel>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard accent="blue" label="平台健康" value={systemStatus?.api.status ?? 'loading'} hint="FastAPI /system/status" />
        <MetricCard
          accent="violet"
          label="Executor"
          value={systemStatus?.executor.status ?? 'unknown'}
          hint={`队列 ${systemStatus?.executor.pending_commands ?? 0}`}
        />
        <MetricCard accent="teal" label="活跃运行" value={activeRuns.length} hint="CREATED / QUEUED / RUNNING" />
        <MetricCard accent="orange" label="在线网关" value={onlineGateways.length} hint="READY / BUSY / DEGRADED" />
        <MetricCard accent="teal" label="运行中采集" value={activeCaptures.length} hint="RUNNING" />
      </div>

      {systemStatus && (
        <div className="grid gap-5 xl:grid-cols-3">
          <Panel>
            <DonutStatusChart
              title="运行状态分布"
              subtitle="活跃 run 应当集中在 RUNNING / STARTING。"
              items={Object.entries(systemStatus.counts.runs)
                .filter(([, value]) => value > 0)
                .map(([label, value]) => ({
                  label,
                  value,
                  color: chartColorForStatus(label)
                }))}
            />
          </Panel>

          <Panel>
            <DonutStatusChart
              title="采集状态分布"
              subtitle="用来观察树莓派是否在稳定落盘。"
              items={Object.entries(systemStatus.counts.captures)
                .filter(([, value]) => value > 0)
                .map(([label, value]) => ({
                  label,
                  value,
                  color: chartColorForStatus(label)
                }))}
            />
          </Panel>

          <Panel title="采集可观测性" subtitle="直接确认当前采集任务和最近写盘记录。">
            <div className="flex flex-col gap-3">
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">运行中采集</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">
                  {systemStatus.capture_observability.running_capture_ids.length}
                </strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">已完成采集</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">
                  {systemStatus.capture_observability.completed_capture_ids.length}
                </strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">最近采集 ID</span>
                <strong className="mt-2 block break-all text-base font-extrabold text-navy-900">
                  {systemStatus.capture_observability.latest_capture_id ?? '-'}
                </strong>
              </div>
            </div>
          </Panel>
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="活跃运行" subtitle="优先处理正在执行或等待执行的 run。">
          {activeRuns.length === 0 ? (
            <EmptyState title="没有活跃运行" description="当前没有 CREATED、QUEUED、RUNNING 状态的场景运行。" />
          ) : (
            <div className="flex flex-col gap-4">
              {activeRuns.slice(0, 5).map((run) => (
                <Link
                  key={run.run_id}
                  className="rounded-[22px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4 transition hover:-translate-y-0.5 hover:shadow-card"
                  to={`/runs/${run.run_id}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <strong className="block text-base font-bold text-navy-900">{run.scenario_name}</strong>
                      <p className="mt-1 text-sm text-secondaryGray-600">{run.map_name}</p>
                    </div>
                    <StatusPill status={run.status} />
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">Run ID</span>
                      <span className="mt-1 block text-sm text-navy-900">{run.run_id}</span>
                    </div>
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">Updated</span>
                      <span className="mt-1 block text-sm text-navy-900">{formatDateTime(run.updated_at_utc)}</span>
                    </div>
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">Tick</span>
                      <span className="mt-1 block text-sm text-navy-900">{run.current_tick ?? '-'}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="网关状态" subtitle="树莓派在线性和最近上报的输入状态。">
          {gateways.length === 0 ? (
            <EmptyState title="没有已注册网关" description="先启动 Pi gateway agent，平台才会收到网关心跳。" />
          ) : (
            <div className="flex flex-col gap-4">
              {gateways.slice(0, 5).map((gateway) => (
                <Link
                  key={gateway.gateway_id}
                  className="rounded-[22px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4 transition hover:-translate-y-0.5 hover:shadow-card"
                  to={`/gateways/${gateway.gateway_id}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <strong className="block text-base font-bold text-navy-900">{gateway.name}</strong>
                      <p className="mt-1 text-sm text-secondaryGray-600">{gateway.gateway_id}</p>
                    </div>
                    <StatusPill status={gateway.status} />
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">Capture</span>
                      <span className="mt-1 block text-sm text-navy-900">
                        {String(gateway.metrics.capture_resolution ?? gateway.address ?? '-')}
                      </span>
                    </div>
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">UDC</span>
                      <span className="mt-1 block text-sm text-navy-900">{String(gateway.metrics.udc_state ?? '-')}</span>
                    </div>
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">Heartbeat</span>
                      <span className="mt-1 block text-sm text-navy-900">{formatDateTime(gateway.last_heartbeat_at_utc)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Panel>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="最近采集任务" subtitle="直接进入采集详情查看 manifest 和帧数量。">
          {captures.length === 0 ? (
            <EmptyState title="还没有采集任务" description="先创建 capture，平台才会追踪树莓派的保存进度。" />
          ) : (
            <div className="flex flex-col gap-4">
              {captures.slice(0, 6).map((capture) => (
                <Link
                  key={capture.capture_id}
                  className="rounded-[22px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4 transition hover:-translate-y-0.5 hover:shadow-card"
                  to={`/captures/${capture.capture_id}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <strong className="block text-base font-bold text-navy-900">{capture.capture_id}</strong>
                      <p className="mt-1 text-sm text-secondaryGray-600">{capture.gateway_id}</p>
                    </div>
                    <StatusPill status={capture.status} />
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">Frames</span>
                      <span className="mt-1 block text-sm text-navy-900">{capture.saved_frames}</span>
                    </div>
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">Format</span>
                      <span className="mt-1 block text-sm text-navy-900">{capture.save_format}</span>
                    </div>
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-[0.14em] text-secondaryGray-500">Updated</span>
                      <span className="mt-1 block text-sm text-navy-900">{formatDateTime(capture.updated_at_utc)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="最近异常" subtitle="把失败和错误状态集中起来，不让用户再到处翻。">
          {recentFailures.length === 0 ? (
            <EmptyState title="没有最近异常" description="当前运行、采集和网关都没有 FAILED / ERROR 记录。" />
          ) : (
            <div className="flex flex-col gap-4">
              {recentFailures.map((item) => (
                <div
                  key={`${item.type}-${item.id}`}
                  className="rounded-[22px] border border-rose-100 bg-rose-50/80 px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <strong className="block text-base font-bold text-navy-900">
                      {item.type} {item.id}
                      </strong>
                      <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{item.message}</p>
                    </div>
                    <StatusPill status={item.status} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
