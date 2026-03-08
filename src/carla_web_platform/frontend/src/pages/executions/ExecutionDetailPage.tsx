import { useEffect, useMemo, useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';

import { listBenchmarkDefinitions } from '../../api/benchmarks';
import { listProjects } from '../../api/projects';
import { cancelRun, getRun, getRunEnvironment, getRunEvents, startRun, stopRun, updateRunEnvironment } from '../../api/runs';
import { listEnvironmentPresets } from '../../api/scenarios';
import type { WeatherConfig } from '../../api/types';
import { EmptyState } from '../../components/common/EmptyState';
import { JsonBlock } from '../../components/common/JsonBlock';
import { KeyValueGrid } from '../../components/common/KeyValueGrid';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, formatRelativeDuration, terminalStatus } from '../../lib/format';
import { deriveRunFps, findBenchmarkDefinition, findProjectRecord, getRunBenchmarkId, getRunChipId } from '../../lib/platform';

const defaultWeather: WeatherConfig = {
  preset: 'ClearNoon'
};

export function ExecutionDetailPage() {
  const { runId = '' } = useParams();
  const queryClient = useQueryClient();

  const [weatherDraft, setWeatherDraft] = useState<WeatherConfig>(defaultWeather);
  const [viewerFriendly, setViewerFriendly] = useState(false);

  const runQuery = useQuery({
    queryKey: ['runs', runId],
    queryFn: () => getRun(runId),
    enabled: Boolean(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && terminalStatus(status) ? false : 3000;
    }
  });

  const eventsQuery = useQuery({
    queryKey: ['runs', runId, 'events'],
    queryFn: () => getRunEvents(runId),
    enabled: Boolean(runId),
    refetchInterval: 3000
  });

  const environmentQuery = useQuery({
    queryKey: ['runs', runId, 'environment'],
    queryFn: () => getRunEnvironment(runId),
    enabled: Boolean(runId),
    refetchInterval: 3000
  });

  const environmentPresetsQuery = useQuery({
    queryKey: ['environment-presets'],
    queryFn: listEnvironmentPresets
  });
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const benchmarkDefinitionsQuery = useQuery({ queryKey: ['benchmark-definitions'], queryFn: listBenchmarkDefinitions });

  useEffect(() => {
    if (environmentQuery.data?.descriptor_weather) {
      setWeatherDraft(environmentQuery.data.runtime_control.weather ?? environmentQuery.data.descriptor_weather);
      setViewerFriendly(Boolean(environmentQuery.data.runtime_control.debug?.viewer_friendly ?? environmentQuery.data.descriptor_debug?.viewer_friendly));
    }
  }, [environmentQuery.data]);

  const stopMutation = useMutation({
    mutationFn: () => stopRun(runId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['runs', runId] });
      void queryClient.invalidateQueries({ queryKey: ['runs'] });
    }
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelRun(runId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['runs', runId] });
      void queryClient.invalidateQueries({ queryKey: ['runs'] });
    }
  });

  const startMutation = useMutation({
    mutationFn: () => startRun(runId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['runs', runId] });
      void queryClient.invalidateQueries({ queryKey: ['runs'] });
      void queryClient.invalidateQueries({ queryKey: ['system-status'] });
    }
  });

  const updateEnvironmentMutation = useMutation({
    mutationFn: () =>
      updateRunEnvironment(runId, {
        weather: weatherDraft,
        debug: { viewer_friendly: viewerFriendly }
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['runs', runId, 'environment'] });
      void queryClient.invalidateQueries({ queryKey: ['runs', runId] });
    }
  });

  const run = runQuery.data;
  const chip = run ? findProjectRecord(projectsQuery.data ?? [], getRunChipId(run)) : null;
  const benchmark = run ? findBenchmarkDefinition(benchmarkDefinitionsQuery.data ?? [], getRunBenchmarkId(run)) : null;
  const fps = run ? deriveRunFps(run) : null;
  const events = eventsQuery.data ?? [];

  const summaryItems = useMemo(() => {
    if (!run) {
      return [];
    }

    return [
      { label: '状态', value: <StatusPill status={run.status} /> },
      { label: '执行 ID', value: run.run_id },
      { label: '芯片项目', value: chip?.name ?? '未标记' },
      { label: '基准任务', value: benchmark?.name ?? '未标记' },
      { label: '场景', value: run.scenario_name },
      { label: '地图', value: run.map_name },
      { label: '绑定设备', value: run.hil_config?.gateway_id ?? '-' },
      { label: '天气预设', value: run.weather?.preset ?? '-' },
      { label: '传感器模板', value: run.sensors?.profile_name ?? '-' },
      { label: '创建时间', value: formatDateTime(run.created_at_utc) },
      { label: '开始时间', value: formatDateTime(run.started_at_utc) },
      { label: '结束时间', value: formatDateTime(run.ended_at_utc) },
      { label: '运行时长', value: formatRelativeDuration(run.started_at_utc, run.ended_at_utc) },
      { label: '失败原因', value: run.error_reason ?? '-' }
    ];
  }, [benchmark?.name, chip?.name, run]);

  if (!runId) {
    return <EmptyState title="缺少执行 ID" description="路由参数里没有 run_id。" />;
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="执行详情"
        eyebrow="Executions / Detail"
        chips={['执行剖面', '事件时间线', '环境热更新']}
        description={run ? `${run.scenario_name} / ${run.map_name}` : runId}
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="horizon-button-secondary" to="/executions">
              返回执行中心
            </Link>
            {run?.status === 'CREATED' && (
              <button className="horizon-button" disabled={startMutation.isPending} onClick={() => startMutation.mutate()} type="button">
                启动执行
              </button>
            )}
            {['STARTING', 'RUNNING', 'PAUSED', 'STOPPING'].includes(run?.status ?? '') && (
              <>
                <button className="horizon-button-secondary" disabled={stopMutation.isPending} onClick={() => stopMutation.mutate()} type="button">
                  停止
                </button>
                <button
                  className="inline-flex min-h-11 items-center justify-center rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm font-bold text-rose-600 transition hover:-translate-y-0.5"
                  disabled={cancelMutation.isPending}
                  onClick={() => cancelMutation.mutate()}
                  type="button"
                >
                  取消
                </button>
              </>
            )}
          </div>
        }
      />

      {!run ? (
        <Panel>
          <p>加载中...</p>
        </Panel>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard accent="blue" label="执行 FPS" value={fps ? fps.toFixed(1) : '待接入'} hint="由 tick / wall time 推导" />
            <MetricCard accent="violet" label="当前 Tick" value={run.current_tick ?? '-'} hint="执行推进深度" />
            <MetricCard accent="teal" label="仿真时间" value={run.sim_time ?? '-'} hint="sim_time 秒" />
            <MetricCard accent="orange" label="墙钟耗时" value={run.wall_elapsed_seconds ? `${run.wall_elapsed_seconds.toFixed(1)} s` : '-'} hint="真实运行耗时" />
          </div>

          <Panel title="执行摘要">
            <KeyValueGrid items={summaryItems} />
          </Panel>

          <div className="grid gap-5 2xl:grid-cols-[minmax(0,1.3fr)_420px]">
            <div className="flex flex-col gap-5">
              <div className="grid gap-5 xl:grid-cols-2">
                <Panel title="执行标签">
                  <JsonBlock value={run.metadata} />
                </Panel>
                <Panel title="评测协议">
                  <JsonBlock value={run.evaluation_profile ?? { message: '当前执行未绑定评测协议。' }} />
                </Panel>
              </div>

              <Panel title="事件时间线" subtitle="直接读取 executor 写入的事件流，适合定位失败和状态切换。">
                {events.length === 0 ? (
                  <EmptyState title="没有事件" description="该执行还没有写入 events.jsonl。" />
                ) : (
                  <div className="timeline">
                    {events.map((event, index) => (
                      <div key={`${event.timestamp}-${index}`} className="timeline__item">
                        <div className="timeline__stamp">
                          <span>{formatDateTime(event.timestamp)}</span>
                          <StatusPill status={event.level} />
                        </div>
                        <div className="timeline__content">
                          <strong>{event.event_type}</strong>
                          <p>{event.message}</p>
                          {Object.keys(event.payload).length > 0 && <JsonBlock compact value={event.payload} />}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Panel>
            </div>

            <div className="flex flex-col gap-5">
              <Panel title="运行环境热更新" subtitle="运行中可以调整天气和 viewer 模式，方便复现实验与观察。">
                <div className="form-grid">
                  <label className="field">
                    <span>天气预设</span>
                    <select
                      value={weatherDraft.preset}
                      onChange={(event) => setWeatherDraft((current) => ({ ...current, preset: event.target.value }))}
                    >
                      {environmentPresetsQuery.data?.map((item) => (
                        <option key={item.preset_id} value={item.weather.preset}>
                          {item.display_name}
                        </option>
                      )) ?? <option value="ClearNoon">Clear Noon</option>}
                    </select>
                  </label>

                  <label className="field">
                    <span>Cloudiness</span>
                    <input
                      type="number"
                      value={weatherDraft.cloudiness ?? 0}
                      onChange={(event) => setWeatherDraft((current) => ({ ...current, cloudiness: Number(event.target.value) }))}
                    />
                  </label>

                  <label className="field">
                    <span>Precipitation</span>
                    <input
                      type="number"
                      value={weatherDraft.precipitation ?? 0}
                      onChange={(event) => setWeatherDraft((current) => ({ ...current, precipitation: Number(event.target.value) }))}
                    />
                  </label>

                  <label className="field">
                    <span>Fog Density</span>
                    <input
                      type="number"
                      value={weatherDraft.fog_density ?? 0}
                      onChange={(event) => setWeatherDraft((current) => ({ ...current, fog_density: Number(event.target.value) }))}
                    />
                  </label>

                  <label className="field">
                    <span>Wetness</span>
                    <input
                      type="number"
                      value={weatherDraft.wetness ?? 0}
                      onChange={(event) => setWeatherDraft((current) => ({ ...current, wetness: Number(event.target.value) }))}
                    />
                  </label>

                  <label className="field field--checkbox">
                    <input checked={viewerFriendly} onChange={(event) => setViewerFriendly(event.target.checked)} type="checkbox" />
                    <span>viewer_friendly</span>
                  </label>
                </div>

                <div className="mt-5 flex flex-wrap gap-3">
                  <button className="horizon-button" disabled={updateEnvironmentMutation.isPending} onClick={() => updateEnvironmentMutation.mutate()} type="button">
                    {updateEnvironmentMutation.isPending ? '更新中...' : '应用环境更新'}
                  </button>
                </div>

                {updateEnvironmentMutation.error && <p className="mt-4 text-sm text-rose-600">{updateEnvironmentMutation.error.message}</p>}
              </Panel>

              <Panel title="当前环境状态">
                <JsonBlock
                  compact
                  value={
                    environmentQuery.data ?? {
                      descriptor_weather: run.weather,
                      descriptor_debug: run.debug,
                      runtime_control: {}
                    }
                  }
                />
              </Panel>

              <Panel title="传感器配置">
                <JsonBlock compact value={run.sensors ?? { enabled: false }} />
              </Panel>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
