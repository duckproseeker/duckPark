import { useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { cancelRun, listRuns, stopRun } from '../../api/runs';
import { getSystemStatus } from '../../api/system';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, formatRelativeDuration, sortByActivity, terminalStatus, truncateMiddle } from '../../lib/format';

export function RunsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');

  const runsQuery = useQuery({ queryKey: ['runs'], queryFn: () => listRuns(), refetchInterval: 5000 });
  const systemQuery = useQuery({
    queryKey: ['system-status'],
    queryFn: getSystemStatus,
    refetchInterval: 3000
  });

  const stopMutation = useMutation({
    mutationFn: (runId: string) => stopRun(runId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['runs'] })
  });
  const cancelMutation = useMutation({
    mutationFn: (runId: string) => cancelRun(runId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['runs'] })
  });

  const runs = sortByActivity(runsQuery.data ?? []);
  const filteredRuns = runs.filter((run) => {
    const statusMatched = !statusFilter || run.status === statusFilter;
    const keyword = searchKeyword.trim().toLowerCase();
    const searchMatched =
      !keyword ||
      run.run_id.toLowerCase().includes(keyword) ||
      run.scenario_name.toLowerCase().includes(keyword) ||
      run.map_name.toLowerCase().includes(keyword) ||
      String(run.hil_config?.gateway_id ?? '').toLowerCase().includes(keyword);
    return statusMatched && searchMatched;
  });

  const activeRunCount = runs.filter((run) => ['CREATED', 'QUEUED', 'STARTING', 'RUNNING', 'STOPPING'].includes(run.status)).length;
  const failedRunCount = runs.filter((run) => run.status === 'FAILED').length;
  const queuedRunCount = runs.filter((run) => run.status === 'QUEUED').length;
  const completedRunCount = runs.filter((run) => run.status === 'COMPLETED').length;

  return (
    <div className="page-stack">
      <PageHeader
        title="Runs"
        description="这里只负责运行队列、状态、事件和故障处理。场景模板、环境参数和传感器 YAML 统一在 Studio 页面配置。"
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="horizon-button" to="/studio">
              Open Studio
            </Link>
            <button className="horizon-button-secondary" onClick={() => void queryClient.invalidateQueries({ queryKey: ['runs'] })} type="button">
              刷新
            </button>
          </div>
        }
      />

      {systemQuery.data?.executor.alive === false && (
        <div className="rounded-[20px] border border-rose-100 bg-rose-50/90 px-5 py-4">
          <strong>Executor 不在线。</strong>
          <span className="mt-1 block text-sm text-rose-600">
            你现在创建 run 后只会进入 QUEUED，直到后台启动 `app.executor.service`。
          </span>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="blue" label="Active Runs" value={activeRunCount} hint="CREATED / RUNNING / STOPPING" />
        <MetricCard accent="orange" label="Queued" value={queuedRunCount} hint="等待 executor 消费" />
        <MetricCard accent="rose" label="Failed" value={failedRunCount} hint="优先检查地图、spawn 和环境配置" />
        <MetricCard accent="teal" label="Completed" value={completedRunCount} hint="已完整结束的运行" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Panel title="Filters" subtitle="保持运行列表短而稳定，优先盯活跃 run。">
          <div className="form-grid">
            <label className="field">
              <span>状态</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">全部</option>
                {['CREATED', 'QUEUED', 'STARTING', 'RUNNING', 'STOPPING', 'COMPLETED', 'FAILED', 'CANCELED'].map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>关键字</span>
              <input
                placeholder="run_id / 场景 / 地图 / gateway"
                value={searchKeyword}
                onChange={(event) => setSearchKeyword(event.target.value)}
              />
            </label>
          </div>

          <div className="mt-5 rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
            <span className="block text-[11px] font-extrabold uppercase tracking-[0.18em] text-secondaryGray-500">Executor</span>
            <strong className="mt-3 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">
              {systemQuery.data?.executor.status ?? 'unknown'}
            </strong>
            <span className="mt-2 block text-sm text-secondaryGray-600">
              Pending {systemQuery.data?.executor.pending_commands ?? 0}
            </span>
          </div>
        </Panel>

        <Panel title="Run Queue" subtitle="以卡片方式显示状态、时间、环境摘要和操作。">
          {filteredRuns.length === 0 ? (
            <EmptyState title="没有匹配的运行" description="当前筛选条件下没有找到 run 记录。" />
          ) : (
            <div className="flex flex-col gap-4">
              {filteredRuns.map((run) => (
                <div key={run.run_id} className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/60 p-5 shadow-card">
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <StatusPill status={run.status} />
                        <Link className="text-sm font-bold text-brand-600" to={`/runs/${run.run_id}`}>
                          {truncateMiddle(run.run_id, 8)}
                        </Link>
                      </div>
                      <strong className="mt-3 block text-xl font-extrabold tracking-[-0.03em] text-navy-900">
                        {run.scenario_name}
                      </strong>
                      <p className="mt-1 text-sm text-secondaryGray-600">
                        {run.map_name} / {run.weather?.preset ?? 'ClearNoon'} / {run.sensors?.profile_name ?? 'No sensor profile'}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      {!terminalStatus(run.status) && (
                        <button
                          className="horizon-button-secondary"
                          disabled={stopMutation.isPending}
                          onClick={() => stopMutation.mutate(run.run_id)}
                          type="button"
                        >
                          停止
                        </button>
                      )}
                      {!terminalStatus(run.status) && (
                        <button
                          className="inline-flex min-h-11 items-center justify-center rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm font-bold text-rose-600 transition hover:-translate-y-0.5"
                          disabled={cancelMutation.isPending}
                          onClick={() => cancelMutation.mutate(run.run_id)}
                          type="button"
                        >
                          取消
                        </button>
                      )}
                      <Link className="horizon-button" to={`/runs/${run.run_id}`}>
                        Detail
                      </Link>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Gateway</span>
                      <strong className="mt-2 block text-sm text-navy-900">{run.hil_config?.gateway_id ?? '-'}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Updated</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatDateTime(run.updated_at_utc)}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Elapsed</span>
                      <strong className="mt-2 block text-sm text-navy-900">
                        {formatRelativeDuration(run.started_at_utc, run.ended_at_utc)}
                      </strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Tick</span>
                      <strong className="mt-2 block text-sm text-navy-900">{run.current_tick ?? '-'}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Sim Time</span>
                      <strong className="mt-2 block text-sm text-navy-900">{run.sim_time ?? '-'} s</strong>
                    </div>
                  </div>
                  {run.error_reason && <p className="mt-4 text-sm text-rose-600">{run.error_reason}</p>}
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
