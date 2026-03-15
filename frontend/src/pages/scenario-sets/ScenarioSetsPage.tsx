import { useEffect, useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { listBenchmarkDefinitions } from '../../api/benchmarks';
import { listProjects } from '../../api/projects';
import {
  launchScenario,
  listEnvironmentPresets,
  listMaps,
  listScenarioCatalog,
  listSensorProfiles
} from '../../api/scenarios';
import type {
  EnvironmentPreset,
  ScenarioCatalogItem,
  SensorProfile,
  ScenarioTemplateParameterSchema,
  ScenarioTemplateParamValue
} from '../../api/types';
import { EmptyState } from '../../components/common/EmptyState';
import { SelectionList } from '../../components/common/SelectionList';
import { StatusPill } from '../../components/common/StatusPill';
import { setWorkflowSelection, useWorkflowSelection } from '../../features/workflow/state';
import { findBenchmarkDefinition, findProjectRecord } from '../../lib/platform';

interface ScenarioSectionRow {
  label: string;
  value: string;
}

interface ScenarioSection {
  title: string;
  rows: ScenarioSectionRow[];
}

const INTEGER_PARAMETER_TYPES = new Set([
  'int',
  'integer',
  'long',
  'short',
  'unsignedint',
  'unsignedinteger',
  'unsignedlong',
  'unsignedshort'
]);

function numberLabel(value: number | undefined) {
  if (typeof value !== 'number') {
    return '-';
  }
  return Number.isInteger(value) ? `${value}` : value.toFixed(2);
}

function buildDefaultTemplateParams(
  parameters: ScenarioTemplateParameterSchema[]
): Record<string, ScenarioTemplateParamValue> {
  const defaults: Record<string, ScenarioTemplateParamValue> = {};
  for (const parameter of parameters) {
    if (parameter.default !== undefined && parameter.default !== null) {
      defaults[parameter.field] = parameter.default;
      continue;
    }
    if (parameter.type === 'boolean') {
      defaults[parameter.field] = false;
      continue;
    }
    if (parameter.type === 'enum' && parameter.options[0]) {
      defaults[parameter.field] = parameter.options[0];
      continue;
    }
    if (parameter.type === 'number') {
      defaults[parameter.field] = parameter.min ?? 0;
      continue;
    }
    defaults[parameter.field] = '';
  }
  return defaults;
}

function formatTemplateParamValue(
  parameter: ScenarioTemplateParameterSchema,
  value: ScenarioTemplateParamValue | undefined
) {
  if (value === undefined || value === null || value === '') {
    return '-';
  }
  if (typeof value === 'boolean') {
    return value ? '是' : '否';
  }
  const rendered = typeof value === 'number' ? numberLabel(value) : `${value}`;
  return parameter.unit ? `${rendered} ${parameter.unit}` : rendered;
}

function clampTemplateNumberValue(
  parameter: ScenarioTemplateParameterSchema,
  value: number
) {
  let next = value;
  if (typeof parameter.min === 'number') {
    next = Math.max(parameter.min, next);
  }
  if (typeof parameter.max === 'number') {
    next = Math.min(parameter.max, next);
  }
  if (INTEGER_PARAMETER_TYPES.has((parameter.parameter_type ?? '').toLowerCase())) {
    next = Math.trunc(next);
  }
  return next;
}

function parseTemplateNumberInput(
  rawValue: string,
  parameter: ScenarioTemplateParameterSchema,
  fallback: number
) {
  if (!rawValue.trim()) {
    const defaultValue =
      typeof parameter.default === 'number' ? parameter.default : fallback;
    return clampTemplateNumberValue(parameter, defaultValue);
  }
  const parsed = Number(rawValue);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return clampTemplateNumberValue(parameter, parsed);
}

function buildTemplateParamsPayload(
  parameters: ScenarioTemplateParameterSchema[],
  values: Record<string, ScenarioTemplateParamValue>
) {
  const payload: Record<string, ScenarioTemplateParamValue> = {};
  for (const parameter of parameters) {
    const currentValue = values[parameter.field];
    if (currentValue === undefined || currentValue === null || currentValue === '') {
      if (parameter.required) {
        const fallback = parameter.default;
        if (fallback !== undefined && fallback !== null && fallback !== '') {
          payload[parameter.field] = fallback;
        }
      }
      continue;
    }
    payload[parameter.field] = currentValue;
  }
  return Object.keys(payload).length > 0 ? payload : undefined;
}

function buildScenarioSections(
  item: ScenarioCatalogItem,
  selectedMapName: string,
  selectedPreset: EnvironmentPreset | undefined,
  selectedSensorProfile: SensorProfile | undefined,
  vehicleCount: number,
  walkerCount: number,
  trafficSeedLabel: string,
  timeoutSeconds: number,
  templateParams: Record<string, ScenarioTemplateParamValue>
): ScenarioSection[] {
  const descriptor = item.descriptor_template;
  const spawn = descriptor.ego_vehicle.spawn_point;

  const sections: ScenarioSection[] = [
    {
      title: '启动配置',
      rows: [
        { label: '测试地图', value: selectedMapName || item.default_map_name },
        { label: '天气预设', value: selectedPreset?.display_name ?? '未选择' },
        { label: '传感器模板', value: selectedSensorProfile?.display_name ?? '未启用' },
        { label: '背景车辆', value: `${vehicleCount}` },
        { label: '背景行人', value: `${walkerCount}` },
        { label: '随机种子', value: trafficSeedLabel },
        { label: '最长运行时长', value: `${timeoutSeconds} s` }
      ]
    },
    {
      title: 'Ego 初始状态',
      rows: [
        { label: '蓝图', value: descriptor.ego_vehicle.blueprint },
        {
          label: 'Spawn',
          value: `x ${numberLabel(spawn.x)}, y ${numberLabel(spawn.y)}, z ${numberLabel(spawn.z)}`
        },
        { label: 'Yaw', value: numberLabel(spawn.yaw) },
        {
          label: '同步模式',
          value: descriptor.sync.enabled
            ? `${numberLabel(descriptor.sync.fixed_delta_seconds)} s / tick`
            : 'Disabled'
        }
      ]
    },
    {
      title: '剧本约束',
      rows: [
        { label: '事件摘要', value: item.preset.event_summary },
        { label: 'Actor 摘要', value: item.preset.actors_summary },
        {
          label: '可调项',
          value: ['地图', '天气', '传感器模板', '背景车辆', '背景行人', '超时']
            .filter((label, index) => {
              const flags = [
                item.launch_capabilities.map_editable,
                item.launch_capabilities.weather_editable,
                item.launch_capabilities.sensor_profile_editable,
                item.launch_capabilities.traffic_vehicle_count_editable,
                item.launch_capabilities.traffic_walker_count_editable,
                item.launch_capabilities.timeout_editable
              ];
              return flags[index];
            })
            .concat(item.parameter_schema.length > 0 ? ['剧本参数'] : [])
            .join(' / ')
        }
      ]
    }
  ];

  if (item.parameter_schema.length > 0) {
    sections.push({
      title: '剧本参数',
      rows: item.parameter_schema.map((parameter) => ({
        label: parameter.label,
        value: formatTemplateParamValue(parameter, templateParams[parameter.field])
      }))
    });
  }

  return sections;
}

function clampCount(value: number, max: number) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.min(max, Math.max(0, Math.trunc(value)));
}

function parseIntegerInput(rawValue: string, fallback: number) {
  if (!rawValue.trim()) {
    return fallback;
  }
  const parsed = Number(rawValue);
  return Number.isFinite(parsed) ? Math.trunc(parsed) : fallback;
}

function parseOptionalSeedInput(rawValue: string) {
  if (!rawValue.trim()) {
    return undefined;
  }
  const parsed = Number(rawValue);
  if (!Number.isFinite(parsed)) {
    return undefined;
  }
  return Math.max(0, Math.trunc(parsed));
}

function buildLaunchTags(
  scenarioId: string,
  projectId: string | null,
  benchmarkDefinitionId: string | null
) {
  return [
    'scenario_runner',
    'scenario_launch',
    scenarioId,
    projectId ? `project:${projectId}` : null,
    benchmarkDefinitionId ? `benchmark:${benchmarkDefinitionId}` : null
  ].filter((value): value is string => Boolean(value));
}

export function ScenarioSetsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const workflow = useWorkflowSelection();
  const [searchParams] = useSearchParams();
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [selectedEnvironmentPresetId, setSelectedEnvironmentPresetId] = useState('');
  const [selectedSensorProfileName, setSelectedSensorProfileName] = useState('');
  const [selectedMapName, setSelectedMapName] = useState('');
  const [vehicleCount, setVehicleCount] = useState(0);
  const [walkerCount, setWalkerCount] = useState(0);
  const [trafficSeedInput, setTrafficSeedInput] = useState('');
  const [timeoutSeconds, setTimeoutSeconds] = useState(120);
  const [autoStart, setAutoStart] = useState(true);
  const [templateParams, setTemplateParams] = useState<Record<string, ScenarioTemplateParamValue>>(
    {}
  );

  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const definitionsQuery = useQuery({
    queryKey: ['benchmark-definitions'],
    queryFn: listBenchmarkDefinitions
  });
  const catalogQuery = useQuery({ queryKey: ['scenario-catalog'], queryFn: listScenarioCatalog });
  const mapsQuery = useQuery({ queryKey: ['maps'], queryFn: listMaps });
  const environmentPresetsQuery = useQuery({
    queryKey: ['environment-presets'],
    queryFn: listEnvironmentPresets
  });
  const sensorProfilesQuery = useQuery({
    queryKey: ['sensor-profiles'],
    queryFn: listSensorProfiles
  });

  const runnableScenarios = (catalogQuery.data ?? []).filter(
    (item) => item.execution_support === 'scenario_runner'
  );
  const environmentPresets = environmentPresetsQuery.data ?? [];
  const sensorProfiles = sensorProfilesQuery.data ?? [];
  const selectedScenario = workflow.scenarioId
    ? runnableScenarios.find((item) => item.scenario_id === workflow.scenarioId) ?? null
    : null;
  const selectedProject = workflow.projectId
    ? findProjectRecord(projectsQuery.data ?? [], workflow.projectId)
    : null;
  const selectedBenchmark = workflow.benchmarkDefinitionId
    ? findBenchmarkDefinition(definitionsQuery.data ?? [], workflow.benchmarkDefinitionId)
    : null;
  const selectedEnvironmentPreset = environmentPresets.find(
    (item) => item.preset_id === selectedEnvironmentPresetId
  );
  const selectedSensorProfile = sensorProfiles.find(
    (item) => item.profile_name === selectedSensorProfileName
  );

  const availableMaps =
    mapsQuery.data?.map((item) => item.map_name) ??
    (selectedScenario ? [selectedScenario.default_map_name] : []);
  const selectedCapabilities = selectedScenario?.launch_capabilities;
  const scenarioSections = selectedScenario
    ? buildScenarioSections(
        selectedScenario,
        selectedMapName || selectedScenario.default_map_name,
        selectedEnvironmentPreset,
        selectedSensorProfile,
        vehicleCount,
        walkerCount,
        trafficSeedInput.trim() || '自动生成',
        timeoutSeconds,
        templateParams
      )
    : [];

  useEffect(() => {
    if (!workflow.scenarioId && runnableScenarios[0]) {
      setWorkflowSelection({ scenarioId: runnableScenarios[0].scenario_id });
    }
  }, [runnableScenarios, workflow.scenarioId]);

  useEffect(() => {
    const scenarioFromQuery = searchParams.get('scenario');
    if (
      scenarioFromQuery &&
      runnableScenarios.some((item) => item.scenario_id === scenarioFromQuery) &&
      scenarioFromQuery !== workflow.scenarioId
    ) {
      setWorkflowSelection({ scenarioId: scenarioFromQuery });
    }
  }, [runnableScenarios, searchParams, workflow.scenarioId]);

  useEffect(() => {
    if (!selectedEnvironmentPresetId && environmentPresets[0]) {
      setSelectedEnvironmentPresetId(environmentPresets[0].preset_id);
    }
  }, [environmentPresets, selectedEnvironmentPresetId]);

  useEffect(() => {
    if (!selectedSensorProfileName && sensorProfiles[0]) {
      setSelectedSensorProfileName(sensorProfiles[0].profile_name);
    }
  }, [selectedSensorProfileName, sensorProfiles]);

  useEffect(() => {
    if (!selectedScenario) {
      return;
    }
    setSelectorOpen(false);
    setSelectedMapName(selectedScenario.default_map_name);
    setVehicleCount(clampCount(selectedScenario.descriptor_template.traffic.num_vehicles, 48));
    setWalkerCount(clampCount(selectedScenario.descriptor_template.traffic.num_walkers, 48));
    setTrafficSeedInput(
      typeof selectedScenario.descriptor_template.traffic.seed === 'number'
        ? `${selectedScenario.descriptor_template.traffic.seed}`
        : ''
    );
    setTimeoutSeconds(selectedScenario.descriptor_template.termination.timeout_seconds);
    setTemplateParams(buildDefaultTemplateParams(selectedScenario.parameter_schema));
    const defaultSensorProfileName = selectedScenario.descriptor_template.sensors.profile_name;
    if (defaultSensorProfileName) {
      setSelectedSensorProfileName(defaultSensorProfileName);
    }
  }, [selectedScenario?.scenario_id]);

  useEffect(() => {
    if (!selectedScenario) {
      return;
    }
    if (!selectedMapName) {
      setSelectedMapName(selectedScenario.default_map_name);
      return;
    }
    if (availableMaps.length > 0 && !availableMaps.includes(selectedMapName)) {
      setSelectedMapName(selectedScenario.default_map_name);
    }
  }, [availableMaps, selectedMapName, selectedScenario?.default_map_name]);

  const launchMutation = useMutation({
    mutationFn: async () => {
      if (!selectedScenario) {
        throw new Error('请先选择运行场景');
      }
      if (!selectedEnvironmentPreset) {
        throw new Error('请先选择天气预设');
      }

      return launchScenario({
        scenario_id: selectedScenario.scenario_id,
        map_name:
          selectedCapabilities?.map_editable === false
            ? selectedScenario.default_map_name
            : selectedMapName || selectedScenario.default_map_name,
        weather:
          selectedCapabilities?.weather_editable === false
            ? undefined
            : selectedEnvironmentPreset.weather,
        traffic: {
          num_vehicles: clampCount(
            vehicleCount,
            selectedCapabilities?.max_vehicle_count ?? 48
          ),
          num_walkers: clampCount(
            walkerCount,
            selectedCapabilities?.max_walker_count ?? 48
          ),
          seed: parseOptionalSeedInput(trafficSeedInput)
        },
        sensor_profile_name:
          selectedCapabilities?.sensor_profile_editable === true
            ? selectedSensorProfileName || undefined
            : undefined,
        template_params: buildTemplateParamsPayload(
          selectedScenario.parameter_schema,
          templateParams
        ),
        timeout_seconds:
          selectedCapabilities?.timeout_editable === false ? undefined : timeoutSeconds,
        auto_start: autoStart,
        metadata: {
          author: 'scenario-sets-ui',
          description: `${selectedScenario.display_name}（Scenario Sets Launch）`,
          tags: buildLaunchTags(
            selectedScenario.scenario_id,
            workflow.projectId,
            workflow.benchmarkDefinitionId
          )
        }
      });
    },
    onSuccess: (run) => {
      setWorkflowSelection({
        scenarioId: run.scenario_name,
        runId: run.run_id
      });
      void queryClient.invalidateQueries({ queryKey: ['runs'] });
      void queryClient.invalidateQueries({ queryKey: ['system-status'] });
      void queryClient.invalidateQueries({ queryKey: ['runs', run.run_id] });
      navigate(`/executions/${run.run_id}`);
    }
  });

  return (
    <div className="page-stack">
      <section className="project-console">
        <header className="project-console__header">
          <div>
            <span className="project-console__eyebrow">场景控制层 / 场景工作台</span>
            <h1>场景启动台</h1>
            <p>前端只负责选择地图、天气、背景参与者和剧本参数，底层的 per-run XOSC 由后端生成并统一交给 ScenarioRunner。</p>
          </div>

          <div className="project-console__header-actions">
            <Link className="horizon-button-secondary" to="/benchmarks" viewTransition>
              返回模板页
            </Link>
            <Link className="horizon-button-secondary" to="/executions" viewTransition>
              查看执行列表
            </Link>
          </div>
        </header>

        <div className="project-console__layout project-console__layout--scenario">
          <div className="project-console__main">
            <section className="project-console__card project-console__picker-bar">
              <div className="project-console__picker-copy">
                <span className="project-console__section-label">场景选择</span>
                <strong>{selectedScenario?.display_name ?? '尚未选择运行场景'}</strong>
                <p>这里选的是测试剧本，底层执行模式和 XOSC 生成过程对前端保持隐藏。</p>
              </div>

              <div className="project-console__picker-actions">
                {selectedScenario && <StatusPill canonical status="READY" />}
                <button
                  className="project-console__picker-button"
                  onClick={() => setSelectorOpen(true)}
                  type="button"
                >
                  {selectedScenario ? '切换场景' : '选择运行场景'}
                </button>
              </div>
            </section>

            {!selectedScenario ? (
              <section className="project-console__card project-console__card--empty">
                <EmptyState
                  description="先通过上方触发器选择场景，再设置地图、天气和背景参与者数量。"
                  title="未选择场景"
                />
              </section>
            ) : (
              <>
                <section className="project-console__card">
                  <header className="project-console__card-header">
                    <div>
                      <span className="project-console__section-label">运行前配置</span>
                      <strong>{selectedScenario.display_name}</strong>
                    </div>
                    <StatusPill canonical status={autoStart ? 'RUNNING' : 'CREATED'} />
                  </header>

                  <div className="project-console__form-stack">
                    <div className="form-grid">
                      <label className="field">
                        <span>测试地图</span>
                        <select
                          disabled={selectedCapabilities?.map_editable === false}
                          onChange={(event) => setSelectedMapName(event.target.value)}
                          value={selectedMapName}
                        >
                          {(availableMaps.length > 0
                            ? availableMaps
                            : [selectedScenario.default_map_name]
                          ).map((mapName) => (
                            <option key={mapName} value={mapName}>
                              {mapName}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="field">
                        <span>天气预设</span>
                        <select
                          disabled={selectedCapabilities?.weather_editable === false}
                          onChange={(event) => setSelectedEnvironmentPresetId(event.target.value)}
                          value={selectedEnvironmentPresetId}
                        >
                          {environmentPresets.map((item) => (
                            <option key={item.preset_id} value={item.preset_id}>
                              {item.display_name}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="field">
                        <span>传感器模板</span>
                        <select
                          disabled={selectedCapabilities?.sensor_profile_editable === false}
                          onChange={(event) => setSelectedSensorProfileName(event.target.value)}
                          value={selectedSensorProfileName}
                        >
                          {sensorProfiles.map((item) => (
                            <option key={item.profile_name} value={item.profile_name}>
                              {item.display_name}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="field">
                        <span>背景车辆</span>
                        <input
                          disabled={selectedCapabilities?.traffic_vehicle_count_editable === false}
                          max={selectedCapabilities?.max_vehicle_count ?? 48}
                          min={0}
                          onChange={(event) =>
                            setVehicleCount(
                              clampCount(
                                parseIntegerInput(event.target.value, vehicleCount),
                                selectedCapabilities?.max_vehicle_count ?? 48
                              )
                            )
                          }
                          type="number"
                          value={vehicleCount}
                        />
                      </label>

                      <label className="field">
                        <span>背景行人</span>
                        <input
                          disabled={selectedCapabilities?.traffic_walker_count_editable === false}
                          max={selectedCapabilities?.max_walker_count ?? 48}
                          min={0}
                          onChange={(event) =>
                            setWalkerCount(
                              clampCount(
                                parseIntegerInput(event.target.value, walkerCount),
                                selectedCapabilities?.max_walker_count ?? 48
                              )
                            )
                          }
                          type="number"
                          value={walkerCount}
                        />
                      </label>

                      <label className="field">
                        <span>随机种子</span>
                        <input
                          min={0}
                          onChange={(event) => setTrafficSeedInput(event.target.value)}
                          placeholder="留空自动生成"
                          type="number"
                          value={trafficSeedInput}
                        />
                        <small className="text-xs text-slate-500">
                          控制背景交通与自由漫游的随机性；留空时后端会为每条 run 自动生成。
                        </small>
                      </label>

                      <label className="field">
                        <span>最长运行时长（秒）</span>
                        <input
                          disabled={selectedCapabilities?.timeout_editable === false}
                          min={1}
                          onChange={(event) =>
                            setTimeoutSeconds(Math.max(1, parseIntegerInput(event.target.value, timeoutSeconds)))
                          }
                          type="number"
                          value={timeoutSeconds}
                        />
                        <small className="text-xs text-slate-500">
                          用于重写场景剧本的最大观察时长，场景会按仿真时间结束。
                        </small>
                      </label>

                      <label className="field field--checkbox">
                        <input
                          checked={autoStart}
                          onChange={(event) => setAutoStart(event.target.checked)}
                          type="checkbox"
                        />
                        <span>创建后立即启动</span>
                      </label>
                    </div>

                    {selectedScenario.parameter_schema.length > 0 && (
                      <div className="space-y-4">
                        <div>
                          <span className="project-console__section-label">剧本参数</span>
                          <p className="text-sm text-slate-500">
                            这些字段由场景模板定义，会直接写入 per-run 的 ScenarioRunner 输入文件。
                          </p>
                        </div>

                        <div className="form-grid">
                          {selectedScenario.parameter_schema.map((parameter) => {
                            if (parameter.type === 'boolean') {
                              return (
                                <label className="field field--checkbox" key={parameter.field}>
                                  <input
                                    checked={Boolean(templateParams[parameter.field])}
                                    onChange={(event) =>
                                      setTemplateParams((current) => ({
                                        ...current,
                                        [parameter.field]: event.target.checked
                                      }))
                                    }
                                    type="checkbox"
                                  />
                                  <span>{parameter.label}</span>
                                </label>
                              );
                            }

                            if (parameter.type === 'enum') {
                              return (
                                <label className="field" key={parameter.field}>
                                  <span>{parameter.label}</span>
                                  <select
                                    onChange={(event) =>
                                      setTemplateParams((current) => ({
                                        ...current,
                                        [parameter.field]: event.target.value
                                      }))
                                    }
                                    value={String(templateParams[parameter.field] ?? '')}
                                  >
                                    {parameter.options.map((option) => (
                                      <option key={option} value={option}>
                                        {option}
                                      </option>
                                    ))}
                                  </select>
                                  {parameter.description && (
                                    <small className="text-xs text-slate-500">
                                      {parameter.description}
                                    </small>
                                  )}
                                </label>
                              );
                            }

                            if (parameter.type === 'number') {
                              const currentValue = templateParams[parameter.field];
                              const fallbackValue =
                                typeof currentValue === 'number'
                                  ? currentValue
                                  : typeof parameter.default === 'number'
                                    ? parameter.default
                                    : 0;
                              return (
                                <label className="field" key={parameter.field}>
                                  <span>{parameter.label}</span>
                                  <input
                                    max={parameter.max ?? undefined}
                                    min={parameter.min ?? undefined}
                                    onChange={(event) =>
                                      setTemplateParams((current) => ({
                                        ...current,
                                        [parameter.field]: parseTemplateNumberInput(
                                          event.target.value,
                                          parameter,
                                          fallbackValue
                                        )
                                      }))
                                    }
                                    step={parameter.step ?? undefined}
                                    type="number"
                                    value={typeof currentValue === 'number' ? currentValue : fallbackValue}
                                  />
                                  {(parameter.description || parameter.unit) && (
                                    <small className="text-xs text-slate-500">
                                      {[parameter.description, parameter.unit ? `单位: ${parameter.unit}` : null]
                                        .filter(Boolean)
                                        .join(' / ')}
                                    </small>
                                  )}
                                </label>
                              );
                            }

                            return (
                              <label className="field" key={parameter.field}>
                                <span>{parameter.label}</span>
                                <input
                                  onChange={(event) =>
                                    setTemplateParams((current) => ({
                                      ...current,
                                      [parameter.field]: event.target.value
                                    }))
                                  }
                                  type="text"
                                  value={String(templateParams[parameter.field] ?? '')}
                                />
                                {parameter.description && (
                                  <small className="text-xs text-slate-500">
                                    {parameter.description}
                                  </small>
                                )}
                              </label>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {mapsQuery.isError && (
                      <p className="text-sm text-amber-600">
                        地图接口当前不可用，先回退到场景默认地图。
                      </p>
                    )}
                    {environmentPresetsQuery.isError && (
                      <p className="text-sm text-rose-600">
                        天气预设加载失败，当前无法安全发起运行。
                      </p>
                    )}
                    {launchMutation.error && (
                      <p className="text-sm text-rose-600">{launchMutation.error.message}</p>
                    )}

                    <div className="mt-1 flex flex-wrap gap-3">
                      <button
                        className="horizon-button"
                        disabled={
                          launchMutation.isPending ||
                          environmentPresetsQuery.isError ||
                          !selectedScenario
                        }
                        onClick={() => launchMutation.mutate()}
                        type="button"
                      >
                        {launchMutation.isPending
                          ? '提交中...'
                          : autoStart
                            ? '创建并启动场景'
                            : '创建场景运行'}
                      </button>
                      <span className="inline-flex items-center rounded-full bg-brand-50 px-4 py-2 text-sm font-semibold text-brand-600">
                        统一进入 ScenarioRunner 执行链路
                      </span>
                    </div>
                  </div>
                </section>

                <section className="project-console__card">
                  <header className="project-console__card-header">
                    <div>
                      <span className="project-console__section-label">场景简报</span>
                      <strong>{selectedScenario.display_name}</strong>
                    </div>
                  </header>

                  <div className="project-console__section-grid project-console__section-grid--scenario">
                    {scenarioSections.map((section) => (
                      <section className="project-console__parameter-card" key={section.title}>
                        <header>
                          <strong>{section.title}</strong>
                        </header>
                        <div className="project-console__parameter-rows">
                          {section.rows.map((row) => (
                            <div
                              className="project-console__parameter-row"
                              key={`${section.title}-${row.label}`}
                            >
                              <span>{row.label}</span>
                              <strong>{row.value}</strong>
                            </div>
                          ))}
                        </div>
                      </section>
                    ))}
                  </div>
                </section>
              </>
            )}
          </div>

          <aside className="project-console__summary">
            <section className="project-console__card">
              <header className="project-console__card-header">
                <div>
                  <span className="project-console__section-label">当前接入</span>
                  <strong>运行上下文</strong>
                </div>
                {selectedScenario && <StatusPill canonical status="READY" />}
              </header>

              {selectedScenario ? (
                <div className="project-console__summary-stack">
                  <p>项目: {selectedProject?.name ?? '未选择项目'}</p>
                  <p>模板: {selectedBenchmark?.name ?? '未选择模板'}</p>
                  <p>地图: {selectedMapName || selectedScenario.default_map_name}</p>
                  <p>天气: {selectedEnvironmentPreset?.display_name ?? '未选择'}</p>
                  <p>背景车辆: {vehicleCount}</p>
                  <p>背景行人: {walkerCount}</p>
                  <p>随机种子: {trafficSeedInput.trim() || '自动生成'}</p>
                  {selectedScenario.parameter_schema.map((parameter) => (
                    <p key={parameter.field}>
                      {parameter.label}:{' '}
                      {formatTemplateParamValue(parameter, templateParams[parameter.field])}
                    </p>
                  ))}
                  <small>{autoStart ? '创建后会直接进入执行队列。' : '创建后停留在 CREATED，等待手动启动。'}</small>
                </div>
              ) : (
                <EmptyState description="选择场景后显示当前运行上下文。" title="没有运行上下文" />
              )}
            </section>

            {selectedScenario && (
              <section className="project-console__card">
                <header className="project-console__card-header">
                  <div>
                    <span className="project-console__section-label">启动提示</span>
                    <strong>场景说明</strong>
                  </div>
                </header>
                <div className="project-console__summary-stack">
                  <p>{selectedScenario.description}</p>
                  {selectedScenario.launch_capabilities.notes.map((note) => (
                    <small key={note}>{note}</small>
                  ))}
                </div>
              </section>
            )}
          </aside>
        </div>

        {selectorOpen && (
          <button
            aria-label="关闭场景选择抽屉"
            className="project-console__drawer-backdrop"
            onClick={() => setSelectorOpen(false)}
            type="button"
          />
        )}

        <aside
          aria-hidden={!selectorOpen}
          className={
            selectorOpen
              ? 'project-console__drawer project-console__drawer--open'
              : 'project-console__drawer'
          }
        >
          <header className="project-console__drawer-header">
            <div>
              <span className="project-console__section-label">选择运行场景</span>
              <strong>场景目录</strong>
            </div>
            <button
              className="project-console__drawer-close"
              onClick={() => setSelectorOpen(false)}
              type="button"
            >
              关闭
            </button>
          </header>

          <div className="project-console__drawer-copy">
            <p>这里展示的是测试剧本本身，不再暴露底层执行模式、XOSC 路径等实现细节。</p>
          </div>

          {catalogQuery.isLoading ? (
            <EmptyState description="正在读取场景目录。" title="场景加载中" />
          ) : catalogQuery.isError ? (
            <EmptyState
              description={catalogQuery.error instanceof Error ? catalogQuery.error.message : '场景接口异常。'}
              title="场景加载失败"
            />
          ) : (
            <SelectionList
              collapseLabel="收起目录"
              emptyDescription="当前环境未返回可执行场景。"
              emptyTitle="没有可执行场景"
              expandLabel="展开目录"
              items={runnableScenarios.map((scenario) => ({
                id: scenario.scenario_id,
                title: scenario.display_name,
                subtitle: scenario.description,
                meta: `${scenario.default_map_name} / ${scenario.parameter_schema.length} 个剧本参数`,
                status: 'READY',
                hint: scenario.scenario_id
              }))}
              maxVisible={8}
              onSelect={(id) => setWorkflowSelection({ scenarioId: id })}
              selectedId={selectedScenario?.scenario_id ?? null}
            />
          )}
        </aside>
      </section>
    </div>
  );
}
