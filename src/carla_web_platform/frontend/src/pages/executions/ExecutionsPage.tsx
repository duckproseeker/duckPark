import { useEffect, useMemo, useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { createBenchmarkTask, listBenchmarkDefinitions } from '../../api/benchmarks';
import { listGateways } from '../../api/gateways';
import { listProjects } from '../../api/projects';
import { cancelRun, listRuns, startRun, stopRun } from '../../api/runs';
import { getSystemStatus } from '../../api/system';
import { listEnvironmentPresets, listEvaluationProfiles, listMaps, listScenarioCatalog, listSensorProfiles } from '../../api/scenarios';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { MultiSelectDropdown } from '../../components/common/MultiSelectDropdown';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { ProgressBar } from '../../components/common/ProgressBar';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, formatRelativeDuration, sortByActivity, terminalStatus, truncateMiddle } from '../../lib/format';
import {
  deriveRunFps,
  findBenchmarkDefinition,
  findProjectRecord,
  getRunBenchmarkId,
  getRunDutModel,
  getRunProjectId
} from '../../lib/platform';

const maxBatchSize = 24;

export function ExecutionsPage() {
  const queryClient = useQueryClient();

  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const benchmarkDefinitionsQuery = useQuery({ queryKey: ['benchmark-definitions'], queryFn: listBenchmarkDefinitions });
  const catalogQuery = useQuery({ queryKey: ['scenario-catalog'], queryFn: listScenarioCatalog });
  const mapsQuery = useQuery({ queryKey: ['maps'], queryFn: listMaps });
  const environmentQuery = useQuery({ queryKey: ['environment-presets'], queryFn: listEnvironmentPresets });
  const sensorProfilesQuery = useQuery({ queryKey: ['sensor-profiles'], queryFn: listSensorProfiles });
  const evaluationProfilesQuery = useQuery({ queryKey: ['evaluation-profiles'], queryFn: listEvaluationProfiles });
  const gatewaysQuery = useQuery({ queryKey: ['gateways'], queryFn: listGateways, refetchInterval: 5000 });
  const runsQuery = useQuery({ queryKey: ['runs'], queryFn: () => listRuns(), refetchInterval: 5000 });
  const systemQuery = useQuery({ queryKey: ['system-status'], queryFn: getSystemStatus, refetchInterval: 3000 });

  const projects = projectsQuery.data ?? [];
  const benchmarkDefinitions = benchmarkDefinitionsQuery.data ?? [];
  const nativeScenarios = (catalogQuery.data ?? []).filter((item) => item.execution_support === 'native');
  const maps = mapsQuery.data ?? [];
  const environmentPresets = environmentQuery.data ?? [];
  const sensorProfiles = sensorProfilesQuery.data ?? [];
  const evaluationProfiles = evaluationProfilesQuery.data ?? [];
  const gateways = gatewaysQuery.data ?? [];
  const runs = sortByActivity(runsQuery.data ?? []);

  const [projectId, setProjectId] = useState('');
  const [benchmarkDefinitionId, setBenchmarkDefinitionId] = useState('');
  const [dutModel, setDutModel] = useState('');
  const [scenarioIds, setScenarioIds] = useState<string[]>([]);
  const [mapNames, setMapNames] = useState<string[]>([]);
  const [environmentIds, setEnvironmentIds] = useState<string[]>([]);
  const [sensorNames, setSensorNames] = useState<string[]>([]);
  const [gatewayId, setGatewayId] = useState('');
  const [evaluationProfileName, setEvaluationProfileName] = useState('');
  const [autoStart, setAutoStart] = useState(false);
  const [batchState, setBatchState] = useState<{ total: number; createdRunIds: string[] } | null>(null);

  useEffect(() => {
    if (!projectId && projects[0]) {
      setProjectId(projects[0].project_id);
    }
  }, [projectId, projects]);

  useEffect(() => {
    if (!benchmarkDefinitionId && benchmarkDefinitions[0]) {
      setBenchmarkDefinitionId(benchmarkDefinitions[0].benchmark_definition_id);
    }
  }, [benchmarkDefinitionId, benchmarkDefinitions]);

  useEffect(() => {
    if (scenarioIds.length === 0 && nativeScenarios[0]) {
      setScenarioIds([nativeScenarios[0].scenario_id]);
    }
  }, [nativeScenarios, scenarioIds.length]);

  useEffect(() => {
    if (mapNames.length === 0 && maps[0]) {
      setMapNames([maps[0].map_name]);
    }
  }, [mapNames.length, maps]);

  useEffect(() => {
    if (environmentIds.length === 0 && environmentPresets[0]) {
      setEnvironmentIds([environmentPresets[0].preset_id]);
    }
  }, [environmentIds.length, environmentPresets]);

  useEffect(() => {
    if (sensorNames.length === 0 && sensorProfiles[0]) {
      setSensorNames([sensorProfiles[0].profile_name]);
    }
  }, [sensorNames.length, sensorProfiles]);

  useEffect(() => {
    if (!gatewayId && gateways[0]) {
      setGatewayId(gateways[0].gateway_id);
    }
  }, [gatewayId, gateways]);

  useEffect(() => {
    if (!evaluationProfileName && evaluationProfiles[0]) {
      setEvaluationProfileName(evaluationProfiles[0].profile_name);
    }
  }, [evaluationProfileName, evaluationProfiles]);

  const selectedProject = findProjectRecord(projects, projectId) ?? projects[0] ?? null;
  const selectedBenchmark = findBenchmarkDefinition(benchmarkDefinitions, benchmarkDefinitionId) ?? benchmarkDefinitions[0] ?? null;
  const selectedEvaluationProfile =
    evaluationProfiles.find((item) => item.profile_name === evaluationProfileName) ?? null;

  const plan = useMemo(() => {
    const selectedScenarios = nativeScenarios.filter((item) => scenarioIds.includes(item.scenario_id));
    const selectedMaps = maps.filter((item) => mapNames.includes(item.map_name));
    const selectedEnvironments = environmentPresets.filter((item) => environmentIds.includes(item.preset_id));
    const selectedSensors = sensorProfiles.filter((item) => sensorNames.includes(item.profile_name));
    const rows: Array<{
      scenarioId: string;
      scenarioName: string;
      displayName: string;
      mapName: string;
      environmentId: string;
      environmentName: string;
      sensorName: string;
    }> = [];

    for (const scenario of selectedScenarios) {
      for (const map of selectedMaps) {
        for (const environment of selectedEnvironments) {
          for (const sensor of selectedSensors) {
            rows.push({
              scenarioId: scenario.scenario_id,
              scenarioName: scenario.scenario_name,
              displayName: scenario.display_name,
              mapName: map.map_name,
              environmentId: environment.preset_id,
              environmentName: environment.display_name,
              sensorName: sensor.profile_name
            });
          }
        }
      }
    }

    return rows;
  }, [environmentIds, environmentPresets, mapNames, maps, nativeScenarios, scenarioIds, sensorNames, sensorProfiles]);

  const createBatchMutation = useMutation({
    mutationFn: async () => {
      if (!selectedProject) {
        throw new Error('缺少项目定义');
      }
      if (!selectedBenchmark) {
        throw new Error('缺少基准任务模板');
      }
      if (plan.length === 0) {
        throw new Error('至少选择 1 个场景、1 张地图、1 个天气和 1 个传感器模板');
      }
      if (plan.length > maxBatchSize) {
        throw new Error(`当前计划会创建 ${plan.length} 个执行，超过单次上限 ${maxBatchSize}`);
      }

      setBatchState({ total: plan.length, createdRunIds: [] });
      const task = await createBenchmarkTask({
        project_id: selectedProject.project_id,
        benchmark_definition_id: selectedBenchmark.benchmark_definition_id,
        dut_model: dutModel.trim() || undefined,
        scenario_matrix: plan.map((row) => ({
          scenario_id: row.scenarioId,
          map_name: row.mapName,
          environment_preset_id: row.environmentId,
          sensor_profile_name: row.sensorName
        })),
        hil_config: gatewayId
          ? {
              mode: 'camera_open_loop',
              gateway_id: gatewayId,
              video_source: 'hdmi_x1301',
              dut_input_mode: 'uvc_camera',
              result_ingest_mode: 'http_push'
            }
          : undefined,
        evaluation_profile_name: selectedEvaluationProfile?.profile_name,
        auto_start: autoStart
      });
      setBatchState({ total: task.planned_run_count, createdRunIds: task.run_ids });
      return task;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['runs'] });
      void queryClient.invalidateQueries({ queryKey: ['system-status'] });
      void queryClient.invalidateQueries({ queryKey: ['benchmark-tasks'] });
    }
  });

  const stopMutation = useMutation({
    mutationFn: (runId: string) => stopRun(runId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['runs'] })
  });

  const startMutation = useMutation({
    mutationFn: (runId: string) => startRun(runId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['runs'] });
      void queryClient.invalidateQueries({ queryKey: ['system-status'] });
    }
  });

  const cancelMutation = useMutation({
    mutationFn: (runId: string) => cancelRun(runId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['runs'] })
  });

  const activeRuns = runs.filter((run) => ['CREATED', 'QUEUED', 'STARTING', 'RUNNING', 'STOPPING'].includes(run.status)).length;
  const queuedRuns = runs.filter((run) => run.status === 'QUEUED').length;
  const completedRuns = runs.filter((run) => run.status === 'COMPLETED').length;
  const recentRuns = runs.slice(0, 12);

  return (
    <div className="page-stack">
      <PageHeader
        title="执行中心"
        eyebrow="Executions / Batch Planner"
        chips={['批量展开', '单 run 复用', '任务编排']}
        description="执行中心负责把测评项目、基准模板、场景矩阵和设备绑定信息提交给后端 benchmark task 模型，再由后端统一展开成多个 run。DUT 型号属于接入信息，只在这里和设备绑定一起登记。"
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="blue" label="计划组合" value={plan.length} hint={`单次建议不超过 ${maxBatchSize} 个 run`} />
        <MetricCard accent="orange" label="待调度" value={queuedRuns} hint="当前还在队列里的执行" />
        <MetricCard accent="teal" label="已完成" value={completedRuns} hint="执行完成的 runs" />
        <MetricCard
          accent="violet"
          label="执行器状态"
          value={systemQuery.data?.executor.status ?? 'UNKNOWN'}
          hint={`运行中 ${activeRuns} / 待命令 ${systemQuery.data?.executor.pending_commands ?? 0}`}
        />
      </div>

      <div className="grid gap-5 2xl:grid-cols-[minmax(0,1.55fr)_420px]">
        <Panel title="批量测评任务创建器" subtitle="这里不再是单个 run 创建表单，而是“测评任务 -> 多个执行”的展开器。">
          <div className="grid gap-5">
            <div className="grid gap-4 xl:grid-cols-2">
              <label className="field">
                <span>所属项目</span>
                <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
                  {projects.map((project) => (
                    <option key={project.project_id} value={project.project_id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>基准任务模板</span>
                <select value={benchmarkDefinitionId} onChange={(event) => setBenchmarkDefinitionId(event.target.value)}>
                  {benchmarkDefinitions.map((template) => (
                    <option key={template.benchmark_definition_id} value={template.benchmark_definition_id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <MultiSelectDropdown
                label="场景池"
                helperText="选择本次批量任务真正要执行的场景"
                items={nativeScenarios.map((item) => ({
                  id: item.scenario_id,
                  label: item.display_name,
                  note: `${item.description} / 默认地图 ${item.default_map_name}`
                }))}
                values={scenarioIds}
                onChange={setScenarioIds}
                placeholder="选择场景"
              />

              <MultiSelectDropdown
                label="地图矩阵"
                helperText="页面显示归一化地图名，后端统一使用对应 Opt 地图"
                items={maps.map((item) => ({
                  id: item.map_name,
                  label: item.display_name,
                  note: item.available_variants?.join(' / ') ?? item.map_name
                }))}
                values={mapNames}
                onChange={setMapNames}
                placeholder="选择地图"
              />

              <MultiSelectDropdown
                label="天气预设"
                helperText="优先选择最能拉开算法差异的天气"
                items={environmentPresets.map((item) => ({
                  id: item.preset_id,
                  label: item.display_name,
                  note: item.description
                }))}
                values={environmentIds}
                onChange={setEnvironmentIds}
                placeholder="选择天气"
              />

              <MultiSelectDropdown
                label="传感器模板"
                helperText="批量任务内保持同一输入模式更利于横向比较"
                items={sensorProfiles.map((item) => ({
                  id: item.profile_name,
                  label: item.display_name,
                  note: item.description
                }))}
                values={sensorNames}
                onChange={setSensorNames}
                placeholder="选择传感器模板"
              />
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <label className="field">
                <span>DUT 型号</span>
                <input
                  onChange={(event) => setDutModel(event.target.value)}
                  placeholder="由测试人员录入，例如演示机 / 开发板样机"
                  value={dutModel}
                />
              </label>

              <label className="field">
                <span>绑定设备</span>
                <select value={gatewayId} onChange={(event) => setGatewayId(event.target.value)}>
                  <option value="">不绑定设备</option>
                  {gateways.map((gateway) => (
                    <option key={gateway.gateway_id} value={gateway.gateway_id}>
                      {gateway.name} ({gateway.gateway_id})
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <label className="field">
                <span>评测协议</span>
                <select value={evaluationProfileName} onChange={(event) => setEvaluationProfileName(event.target.value)}>
                  {evaluationProfiles.map((profile) => (
                    <option key={profile.profile_name} value={profile.profile_name}>
                      {profile.display_name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field field--checkbox">
                <input checked={autoStart} onChange={(event) => setAutoStart(event.target.checked)} type="checkbox" />
                <span>创建后自动启动所有 run</span>
              </label>
            </div>
          </div>
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel title="任务展开预览" subtitle="先确认矩阵，再批量创建。">
            <div className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
              <span className="block text-sm text-secondaryGray-500">当前模板</span>
              <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">
                {selectedBenchmark?.name ?? '-'}
              </strong>
              <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{selectedBenchmark?.description ?? '-'}</p>
            </div>

            <div className="grid gap-3">
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">所属项目</span>
                <strong className="mt-2 block text-lg font-extrabold text-navy-900">
                  {selectedProject?.name ?? projectId}
                </strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">DUT 型号</span>
                <strong className="mt-2 block text-lg font-extrabold text-navy-900">{dutModel.trim() || '未登记'}</strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">将创建 run 数</span>
                <strong className="mt-2 block text-lg font-extrabold text-navy-900">{plan.length}</strong>
              </div>
            </div>

            {batchState && (
              <div className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">创建进度</span>
                <div className="mt-3">
                  <ProgressBar
                    label={`${batchState.createdRunIds.length}/${batchState.total}`}
                    max={batchState.total}
                    value={batchState.createdRunIds.length}
                  />
                </div>
              </div>
            )}

            {plan.length > maxBatchSize && (
              <div className="rounded-[20px] border border-rose-100 bg-rose-50/90 px-4 py-4 text-sm leading-6 text-rose-600">
                当前批量计划会生成 {plan.length} 个 run，超过单次上限 {maxBatchSize}。请减少场景、地图、天气或传感器组合。
              </div>
            )}

            <div className="flex flex-wrap gap-3">
              <button
                className="horizon-button"
                disabled={createBatchMutation.isPending || plan.length === 0 || plan.length > maxBatchSize}
                onClick={() => createBatchMutation.mutate()}
                type="button"
              >
                {createBatchMutation.isPending ? '批量创建中...' : '创建测评任务'}
              </button>
              <Link className="horizon-button-secondary" to="/scenario-sets">
                回场景集调整矩阵
              </Link>
            </div>

            {createBatchMutation.error && <p className="text-sm text-rose-600">{createBatchMutation.error.message}</p>}

            <div className="grid gap-3">
              {plan.slice(0, 10).map((row, index) => (
                <div key={`${row.scenarioId}-${row.mapName}-${row.environmentId}-${row.sensorName}-${index}`} className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                  <strong className="block text-sm font-bold text-navy-900">{row.displayName}</strong>
                  <p className="mt-1 text-xs text-secondaryGray-500">
                    {row.mapName} / {row.environmentName} / {row.sensorName}
                  </p>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>

      <Panel title="执行列表" subtitle="批量任务会最终沉淀为多个 run。这里按执行视角查看状态、项目标签、DUT 登记和调度动作。">
        {recentRuns.length === 0 ? (
          <EmptyState title="没有执行记录" description="先创建测评任务，平台才会开始生成执行列表。" />
        ) : (
          <div className="flex flex-col gap-4">
                    {recentRuns.map((run) => {
              const project = findProjectRecord(projects, getRunProjectId(run));
              const benchmark = findBenchmarkDefinition(benchmarkDefinitions, getRunBenchmarkId(run));
              const dutModelValue = getRunDutModel(run);
              const fps = deriveRunFps(run);

              return (
                <div key={run.run_id} className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/60 p-5 shadow-card">
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <StatusPill status={run.status} />
                        {project && <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600">{project.name}</span>}
                        {dutModelValue && <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-secondaryGray-600">{dutModelValue}</span>}
                        {benchmark && <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-600">{benchmark.name}</span>}
                      </div>
                      <strong className="mt-3 block text-xl font-extrabold tracking-[-0.03em] text-navy-900">{run.scenario_name}</strong>
                      <p className="mt-1 text-sm text-secondaryGray-600">
                        {run.map_name} / {run.sensors?.profile_name ?? '未指定传感器模板'}
                      </p>
                      <p className="mt-1 text-xs text-secondaryGray-500">{truncateMiddle(run.run_id, 10)}</p>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      {run.status === 'CREATED' && (
                        <button
                          className="horizon-button"
                          disabled={startMutation.isPending}
                          onClick={() => startMutation.mutate(run.run_id)}
                          type="button"
                        >
                          启动
                        </button>
                      )}
                      {['STARTING', 'RUNNING', 'PAUSED', 'STOPPING'].includes(run.status) && (
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
                      <Link className="horizon-button" to={`/executions/${run.run_id}`}>
                        详情
                      </Link>
                    </div>
                  </div>

                    <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">设备</span>
                      <strong className="mt-2 block text-sm text-navy-900">{run.hil_config?.gateway_id ?? '-'}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">更新时间</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatDateTime(run.updated_at_utc)}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">时长</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatRelativeDuration(run.started_at_utc, run.ended_at_utc)}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Tick</span>
                      <strong className="mt-2 block text-sm text-navy-900">{run.current_tick ?? '-'}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">FPS</span>
                      <strong className="mt-2 block text-sm text-navy-900">{fps ? fps.toFixed(1) : '待接入'}</strong>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Panel>
    </div>
  );
}
