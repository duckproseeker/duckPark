import { useEffect, useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';

import { listGateways } from '../../api/gateways';
import { createRun, startRun } from '../../api/runs';
import { listEnvironmentPresets, listEvaluationProfiles, listMaps, listScenarioCatalog, listSensorProfiles } from '../../api/scenarios';
import type {
  CreateRunPayload,
  EnvironmentPreset,
  ScenarioCatalogItem,
  ScenarioDescriptor,
  SensorProfile
} from '../../api/types';
import { EmptyState } from '../../components/common/EmptyState';
import { JsonBlock } from '../../components/common/JsonBlock';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';

function cloneDescriptor(descriptor: ScenarioDescriptor): ScenarioDescriptor {
  return JSON.parse(JSON.stringify(descriptor)) as ScenarioDescriptor;
}

function buildDescriptor(
  scenario: ScenarioCatalogItem,
  environmentPreset: EnvironmentPreset | undefined,
  sensorProfile: SensorProfile | undefined,
  mapName: string
): ScenarioDescriptor {
  const descriptor = cloneDescriptor(scenario.descriptor_template);
  descriptor.map_name = scenario.preset.locked_map_name || scenario.default_map_name;
  descriptor.metadata = {
    ...descriptor.metadata,
    author: 'react-studio',
    description: `${scenario.display_name}（Studio / ScenarioRunner 创建）`
  };
  return descriptor;
}

export function StudioPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const catalogQuery = useQuery({ queryKey: ['scenario-catalog'], queryFn: listScenarioCatalog });
  const mapsQuery = useQuery({ queryKey: ['maps'], queryFn: listMaps });
  const gatewaysQuery = useQuery({ queryKey: ['gateways'], queryFn: listGateways, refetchInterval: 5000 });
  const profilesQuery = useQuery({ queryKey: ['evaluation-profiles'], queryFn: listEvaluationProfiles });
  const environmentPresetsQuery = useQuery({
    queryKey: ['environment-presets'],
    queryFn: listEnvironmentPresets
  });
  const sensorProfilesQuery = useQuery({ queryKey: ['sensor-profiles'], queryFn: listSensorProfiles });

  const catalogItems = catalogQuery.data ?? [];
  const runnerScenarios = catalogItems.filter((item) => item.execution_support === 'scenario_runner');
  const environmentPresets = environmentPresetsQuery.data ?? [];
  const sensorProfiles = sensorProfilesQuery.data ?? [];
  const evaluationProfiles = profilesQuery.data ?? [];
  const gateways = gatewaysQuery.data ?? [];
  const maps = mapsQuery.data ?? [];

  const [selectedScenarioId, setSelectedScenarioId] = useState('');
  const [selectedEnvironmentPresetId, setSelectedEnvironmentPresetId] = useState('');
  const [selectedSensorProfileName, setSelectedSensorProfileName] = useState('');
  const [selectedGatewayId, setSelectedGatewayId] = useState('');
  const [selectedMapName, setSelectedMapName] = useState('');
  const [selectedEvaluationProfile, setSelectedEvaluationProfile] = useState('');
  const [autoStart, setAutoStart] = useState(true);

  useEffect(() => {
    if (!selectedScenarioId && runnerScenarios[0]) {
      setSelectedScenarioId(runnerScenarios[0].scenario_id);
    }
  }, [runnerScenarios, selectedScenarioId]);

  useEffect(() => {
    if (!selectedEnvironmentPresetId && environmentPresets[0]) {
      setSelectedEnvironmentPresetId(environmentPresets[0].preset_id);
    }
  }, [environmentPresets, selectedEnvironmentPresetId]);

  useEffect(() => {
    if (!selectedSensorProfileName && sensorProfiles[0]) {
      setSelectedSensorProfileName(sensorProfiles[0].profile_name);
    }
  }, [sensorProfiles, selectedSensorProfileName]);

  useEffect(() => {
    if (!selectedGatewayId && gateways[0]) {
      setSelectedGatewayId(gateways[0].gateway_id);
    }
  }, [gateways, selectedGatewayId]);

  useEffect(() => {
    if (!selectedEvaluationProfile && evaluationProfiles[0]) {
      setSelectedEvaluationProfile(evaluationProfiles[0].profile_name);
    }
  }, [evaluationProfiles, selectedEvaluationProfile]);

  const selectedScenario = catalogItems.find((item) => item.scenario_id === selectedScenarioId);
  const selectedEnvironmentPreset = environmentPresets.find(
    (item) => item.preset_id === selectedEnvironmentPresetId
  );
  const selectedSensorProfile = sensorProfiles.find(
    (item) => item.profile_name === selectedSensorProfileName
  );
  const selectedEvaluation = evaluationProfiles.find(
    (item) => item.profile_name === selectedEvaluationProfile
  );

  useEffect(() => {
    if (selectedScenario) {
      setSelectedMapName(selectedScenario.default_map_name);
    }
  }, [selectedScenario]);

  const descriptorPreview = selectedScenario
    ? buildDescriptor(
        selectedScenario,
        selectedEnvironmentPreset,
        selectedSensorProfile,
        selectedMapName || selectedScenario.default_map_name
      )
    : null;

  const createMutation = useMutation({
    mutationFn: async () => {
      if (!selectedScenario || !descriptorPreview) {
        throw new Error('请选择场景模板');
      }

      const payload: CreateRunPayload = {
        descriptor: descriptorPreview
      };

      if (selectedGatewayId) {
        payload.hil_config = {
          mode: 'camera_open_loop',
          gateway_id: selectedGatewayId,
          video_source: 'hdmi_x1301',
          dut_input_mode: 'uvc_camera',
          result_ingest_mode: 'http_push'
        };
      }
      if (selectedEvaluation) {
        payload.evaluation_profile = {
          profile_name: selectedEvaluation.profile_name,
          metrics: selectedEvaluation.metrics,
          iou_threshold: selectedEvaluation.iou_threshold,
          classes: selectedEvaluation.classes
        };
      }

      const created = await createRun(payload);
      if (autoStart) {
        await startRun(created.run_id);
      }
      return created.run_id;
    },
    onSuccess: (runId) => {
      void queryClient.invalidateQueries({ queryKey: ['runs'] });
      void queryClient.invalidateQueries({ queryKey: ['system-status'] });
      void navigate(`/runs/${runId}`);
    }
  });

  return (
    <div className="page-stack">
      <PageHeader
        title="Studio"
        description="把场景模板、环境预设、传感器 YAML 和 HIL 绑定放到一个地方配置，再由 Runs 页面负责生命周期和故障处理。"
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="horizon-button-secondary" to="/scenario-library">
              打开场景库
            </Link>
            <Link className="horizon-button-secondary" to="/runs">
              查看运行列表
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="blue" label="ScenarioRunner" value={runnerScenarios.length} hint="当前目录里的统一执行模板" />
        <MetricCard accent="violet" label="Linked XOSC" value={catalogItems.filter((item) => item.source.resolved_xosc_path).length} hint="能解析到 xosc 文件的模板数" />
        <MetricCard accent="teal" label="Gateways" value={gateways.length} hint="可绑定到 run 的网关数量" />
        <MetricCard accent="orange" label="Eval Profiles" value={evaluationProfiles.length} hint="可附带的评测模板" />
      </div>

      <div className="grid gap-5 2xl:grid-cols-[minmax(0,1.5fr)_420px]">
        <div className="flex flex-col gap-5">
          <Panel title="Scenario Selection" subtitle="所有场景统一由 ScenarioRunner 执行；Studio 这里只负责创建 run 并绑定 HIL / 评测模板。">
            {catalogItems.length === 0 ? (
              <EmptyState title="没有场景目录" description="后端尚未返回可用场景库。" />
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                {catalogItems.slice(0, 10).map((item) => (
                  <button
                    key={item.scenario_id}
                    className={[
                      'rounded-[24px] border p-5 text-left transition',
                      item.scenario_id === selectedScenarioId
                        ? 'border-brand-200 bg-brand-50/70 shadow-card'
                        : 'border-secondaryGray-200 bg-secondaryGray-50/60 hover:-translate-y-0.5 hover:shadow-card'
                    ].join(' ')}
                    onClick={() => setSelectedScenarioId(item.scenario_id)}
                    type="button"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                      <strong className="block text-lg font-extrabold tracking-[-0.03em] text-navy-900">
                        {item.display_name}
                      </strong>
                      <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{item.description}</p>
                    </div>
                      <StatusPill status="READY" />
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold text-secondaryGray-500">
                      <span className="rounded-full bg-white px-3 py-1">{item.default_map_name}</span>
                      <span className="rounded-full bg-white px-3 py-1">{item.source.provider}</span>
                      {item.source.class_name && <span className="rounded-full bg-white px-3 py-1">{item.source.class_name}</span>}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Panel>

          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Environment Presets" subtitle="当前统一由 ScenarioRunner 执行，这里只保留目录展示，不覆写官方场景参数。">
              <div className="flex flex-col gap-3">
                {environmentPresets.map((item) => (
                  <button
                    key={item.preset_id}
                    className={[
                      'rounded-[20px] border p-4 text-left transition',
                      item.preset_id === selectedEnvironmentPresetId
                        ? 'border-brand-200 bg-brand-50/70'
                        : 'border-secondaryGray-200 bg-secondaryGray-50/60 hover:-translate-y-0.5 hover:shadow-card'
                    ].join(' ')}
                    onClick={() => setSelectedEnvironmentPresetId(item.preset_id)}
                    type="button"
                  >
                    <strong className="block text-sm font-extrabold text-navy-900">{item.display_name}</strong>
                    <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{item.description}</p>
                  </button>
                ))}
              </div>
            </Panel>

            <Panel title="Sensor Profiles" subtitle="当前仅展示平台传感器模板目录，不直接注入到 ScenarioRunner 模板。">
              <div className="flex flex-col gap-3">
                {sensorProfiles.map((item) => (
                  <button
                    key={item.profile_name}
                    className={[
                      'rounded-[20px] border p-4 text-left transition',
                      item.profile_name === selectedSensorProfileName
                        ? 'border-brand-200 bg-brand-50/70'
                        : 'border-secondaryGray-200 bg-secondaryGray-50/60 hover:-translate-y-0.5 hover:shadow-card'
                    ].join(' ')}
                    onClick={() => setSelectedSensorProfileName(item.profile_name)}
                    type="button"
                  >
                    <strong className="block text-sm font-extrabold text-navy-900">{item.display_name}</strong>
                    <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{item.description}</p>
                    <span className="mt-3 inline-flex rounded-full bg-white px-3 py-1 text-xs font-semibold text-secondaryGray-600">
                      {item.sensors.length} sensors
                    </span>
                  </button>
                ))}
              </div>
            </Panel>
          </div>
        </div>

        <div className="flex flex-col gap-5">
          <Panel title="Launch Configuration" subtitle="最终会写成 run descriptor 并进入 executor 队列。">
            <div className="form-grid">
              <label className="field">
                <span>地图</span>
                <select disabled value={selectedScenario?.preset.locked_map_name ?? selectedMapName}>
                  <option value={selectedScenario?.preset.locked_map_name ?? ''}>
                    {selectedScenario?.preset.locked_map_name ?? '请先选择场景'}
                  </option>
                </select>
              </label>

              <label className="field">
                <span>绑定网关</span>
                <select value={selectedGatewayId} onChange={(event) => setSelectedGatewayId(event.target.value)}>
                  <option value="">不绑定网关</option>
                  {gateways.map((item) => (
                    <option key={item.gateway_id} value={item.gateway_id}>
                      {item.name} ({item.gateway_id})
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>评测模板</span>
                <select
                  value={selectedEvaluationProfile}
                  onChange={(event) => setSelectedEvaluationProfile(event.target.value)}
                >
                  {evaluationProfiles.map((item) => (
                    <option key={item.profile_name} value={item.profile_name}>
                      {item.display_name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field field--checkbox">
                <input checked={autoStart} onChange={(event) => setAutoStart(event.target.checked)} type="checkbox" />
                <span>创建后立即启动</span>
              </label>
            </div>

            {createMutation.error && <p className="mt-4 text-sm text-rose-600">{createMutation.error.message}</p>}
            <div className="mt-5 flex flex-wrap gap-3">
              <button
                className="horizon-button"
                disabled={createMutation.isPending || !selectedScenario}
                onClick={() => createMutation.mutate()}
                type="button"
              >
                {createMutation.isPending ? '提交中...' : autoStart ? 'Create & Start Run' : 'Create Run'}
              </button>
              <span className="inline-flex items-center rounded-full bg-brand-50 px-4 py-2 text-sm font-semibold text-brand-600">
                统一进入 ScenarioRunner 执行链路
              </span>
            </div>
          </Panel>

          <Panel title="Descriptor Preview" subtitle="这里是最终发给后端的场景描述。">
            {descriptorPreview ? <JsonBlock compact value={descriptorPreview} /> : <EmptyState title="未选择场景" description="先选择一个场景模板。" />}
          </Panel>

          <Panel title="Sensor YAML Preview" subtitle="用于核对传感器布局、类型和相机分辨率。">
            {selectedSensorProfile ? (
              <pre className="json-block json-block--compact">{selectedSensorProfile.raw_yaml}</pre>
            ) : (
              <EmptyState title="未选择传感器模板" description="先选择一个 YAML 传感器模板。" />
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
