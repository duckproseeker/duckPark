import { useEffect, useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { listScenarioCatalog, listSensorProfiles, saveSensorProfile } from '../../api/scenarios';
import type {
  ScenarioCatalogItem,
  SensorProfile,
  SensorProfileSavePayload,
  SensorSpec
} from '../../api/types';
import { EmptyState } from '../../components/common/EmptyState';
import { JsonBlock } from '../../components/common/JsonBlock';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';

interface EditableSensorSpec extends SensorSpec {
  attributes_text: string;
}

interface SensorProfileEditorState {
  profile_name: string;
  display_name: string;
  description: string;
  vehicle_model: string;
  metadata_text: string;
  sensors: EditableSensorSpec[];
  is_new: boolean;
}

const SENSOR_NUMBER_FIELDS: Array<{
  key: keyof SensorSpec;
  label: string;
  step?: number;
  min?: number;
}> = [
  { key: 'x', label: 'X', step: 0.01 },
  { key: 'y', label: 'Y', step: 0.01 },
  { key: 'z', label: 'Z', step: 0.01 },
  { key: 'roll', label: 'Roll', step: 0.1 },
  { key: 'pitch', label: 'Pitch', step: 0.1 },
  { key: 'yaw', label: 'Yaw', step: 0.1 },
  { key: 'width', label: 'Width', min: 1, step: 1 },
  { key: 'height', label: 'Height', min: 1, step: 1 },
  { key: 'fov', label: 'FOV', min: 0.1, step: 0.1 },
  { key: 'horizontal_fov', label: 'Horizontal FOV', min: 0.1, step: 0.1 },
  { key: 'vertical_fov', label: 'Vertical FOV', min: 0.1, step: 0.1 },
  { key: 'range', label: 'Range', min: 0.1, step: 0.1 },
  { key: 'channels', label: 'Channels', min: 1, step: 1 },
  { key: 'points_per_second', label: 'Points / s', min: 1, step: 1 },
  { key: 'rotation_frequency', label: 'Rotation Hz', min: 0.1, step: 0.1 },
  { key: 'reading_frequency', label: 'Reading Hz', min: 0.1, step: 0.1 }
];

function buildEmptySensor(type = 'sensor.camera.rgb'): EditableSensorSpec {
  return {
    id: '',
    type,
    x: 0,
    y: 0,
    z: 0,
    roll: 0,
    pitch: 0,
    yaw: 0,
    width: type.startsWith('sensor.camera.') ? 1920 : undefined,
    height: type.startsWith('sensor.camera.') ? 1080 : undefined,
    fov: type.startsWith('sensor.camera.') ? 90 : undefined,
    range: type === 'sensor.lidar.ray_cast' ? 85 : undefined,
    channels: type === 'sensor.lidar.ray_cast' ? 64 : undefined,
    points_per_second: type === 'sensor.lidar.ray_cast' ? 600000 : undefined,
    rotation_frequency: type === 'sensor.lidar.ray_cast' ? 10 : undefined,
    attributes_text: '{}'
  };
}

function sanitizeMetadata(metadata: Record<string, unknown>) {
  const next = { ...metadata };
  delete next.vehicle_model;
  return next;
}

function profileToEditor(profile: SensorProfile): SensorProfileEditorState {
  return {
    profile_name: profile.profile_name,
    display_name: profile.display_name,
    description: profile.description,
    vehicle_model: profile.vehicle_model ?? '',
    metadata_text: JSON.stringify(sanitizeMetadata(profile.metadata), null, 2),
    sensors: profile.sensors.map((sensor) => ({
      ...sensor,
      attributes_text: JSON.stringify(sensor.attributes ?? {}, null, 2)
    })),
    is_new: false
  };
}

function createEmptyEditor(): SensorProfileEditorState {
  return {
    profile_name: '',
    display_name: '',
    description: '',
    vehicle_model: '',
    metadata_text: '{}',
    sensors: [buildEmptySensor()],
    is_new: true
  };
}

function parseJsonObject(raw: string, label: string) {
  const normalized = raw.trim();
  if (!normalized) {
    return {};
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(normalized);
  } catch (error) {
    throw new Error(`${label} 必须是合法 JSON`);
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error(`${label} 必须是 JSON 对象`);
  }
  return parsed as Record<string, unknown>;
}

function buildSavePayload(editor: SensorProfileEditorState): SensorProfileSavePayload {
  const metadata = parseJsonObject(editor.metadata_text, '元数据');
  if (editor.vehicle_model.trim()) {
    metadata.vehicle_model = editor.vehicle_model.trim();
  }

  return {
    profile_name: editor.profile_name.trim(),
    display_name: editor.display_name.trim(),
    description: editor.description.trim(),
    vehicle_model: editor.vehicle_model.trim() || null,
    metadata,
    sensors: editor.sensors.map((sensor, index) => ({
      id: sensor.id.trim() || `Sensor${index + 1}`,
      type: sensor.type.trim(),
      x: sensor.x,
      y: sensor.y,
      z: sensor.z,
      roll: sensor.roll,
      pitch: sensor.pitch,
      yaw: sensor.yaw,
      width: sensor.width,
      height: sensor.height,
      fov: sensor.fov,
      horizontal_fov: sensor.horizontal_fov,
      vertical_fov: sensor.vertical_fov,
      range: sensor.range,
      channels: sensor.channels,
      points_per_second: sensor.points_per_second,
      rotation_frequency: sensor.rotation_frequency,
      reading_frequency: sensor.reading_frequency,
      attributes: parseJsonObject(sensor.attributes_text, `传感器 ${sensor.id || index + 1} 的高级属性`)
    }))
  };
}

function countSensors(profiles: SensorProfile[]) {
  return profiles.reduce((total, profile) => total + profile.sensors.length, 0);
}

function parseOptionalNumber(rawValue: string) {
  if (!rawValue.trim()) {
    return undefined;
  }
  const parsed = Number(rawValue);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function StudioPage() {
  const queryClient = useQueryClient();
  const sensorProfilesQuery = useQuery({
    queryKey: ['sensor-profiles'],
    queryFn: listSensorProfiles
  });
  const catalogQuery = useQuery({
    queryKey: ['scenario-catalog'],
    queryFn: listScenarioCatalog
  });

  const sensorProfiles = sensorProfilesQuery.data ?? [];
  const catalogItems = catalogQuery.data ?? [];
  const editableScenarioCount = catalogItems.filter(
    (item) => item.launch_capabilities.sensor_profile_editable
  ).length;
  const vehicleBoundCount = sensorProfiles.filter((item) => item.vehicle_model).length;

  const [selectedProfileName, setSelectedProfileName] = useState('');
  const [editor, setEditor] = useState<SensorProfileEditorState>(createEmptyEditor);

  useEffect(() => {
    if (!selectedProfileName && sensorProfiles[0]) {
      setSelectedProfileName(sensorProfiles[0].profile_name);
      setEditor(profileToEditor(sensorProfiles[0]));
    }
  }, [selectedProfileName, sensorProfiles]);

  const selectedProfile =
    sensorProfiles.find((item) => item.profile_name === selectedProfileName) ?? null;

  const previewPayload = (() => {
    try {
      return buildSavePayload(editor);
    } catch (error) {
      return { preview_error: error instanceof Error ? error.message : '预览生成失败' };
    }
  })();

  const saveMutation = useMutation({
    mutationFn: async () => saveSensorProfile(buildSavePayload(editor)),
    onSuccess: async (savedProfile) => {
      setSelectedProfileName(savedProfile.profile_name);
      setEditor(profileToEditor(savedProfile));
      await queryClient.invalidateQueries({ queryKey: ['sensor-profiles'] });
    }
  });

  function selectProfile(profile: SensorProfile) {
    setSelectedProfileName(profile.profile_name);
    setEditor(profileToEditor(profile));
  }

  function updateEditor<K extends keyof SensorProfileEditorState>(
    key: K,
    value: SensorProfileEditorState[K]
  ) {
    setEditor((current) => ({ ...current, [key]: value }));
  }

  function updateSensor(
    index: number,
    updater: (current: EditableSensorSpec) => EditableSensorSpec
  ) {
    setEditor((current) => ({
      ...current,
      sensors: current.sensors.map((sensor, sensorIndex) =>
        sensorIndex === index ? updater(sensor) : sensor
      )
    }));
  }

  function addSensor(type = 'sensor.camera.rgb') {
    setEditor((current) => ({
      ...current,
      sensors: [...current.sensors, buildEmptySensor(type)]
    }));
  }

  function removeSensor(index: number) {
    setEditor((current) => ({
      ...current,
      sensors:
        current.sensors.length > 1
          ? current.sensors.filter((_, sensorIndex) => sensorIndex !== index)
          : current.sensors
    }));
  }

  const selectedProfileScenarioDefaults = catalogItems.filter((item) => {
    return (
      item.descriptor_template.sensors.profile_name === selectedProfileName ||
      (selectedProfileName && item.launch_capabilities.sensor_profile_editable)
    );
  });

  return (
    <div className="page-stack">
      <PageHeader
        title="Studio"
        description="把传感器模板作为运维资产维护。场景页只选择 profile_name，具体坐标、分辨率和高级参数都在这里按车型固定。"
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="horizon-button-secondary" to="/scenario-sets">
              去场景集使用模板
            </Link>
            <button
              className="horizon-button"
              onClick={() => {
                setSelectedProfileName('');
                setEditor(createEmptyEditor());
              }}
              type="button"
            >
              新建模板
            </button>
          </div>
        }
        chips={['运维配置', '传感器模板', '车型绑定']}
        eyebrow="Operations Workspace"
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="blue" label="传感器模板" value={sensorProfiles.length} hint="YAML 模板总数" />
        <MetricCard accent="teal" label="车型绑定" value={vehicleBoundCount} hint="已声明 vehicle_model 的模板数" />
        <MetricCard accent="violet" label="传感器总数" value={countSensors(sensorProfiles)} hint="所有模板里的传感器数量" />
        <MetricCard accent="orange" label="可用场景" value={editableScenarioCount} hint="支持直接选择传感器模板的场景数" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[340px_minmax(0,1fr)]">
        <Panel
          title="模板列表"
          subtitle="左侧管理模板资产，右侧编辑具体传感器参数。"
          actions={
            sensorProfilesQuery.isLoading ? <span className="text-xs text-slate-400">加载中...</span> : null
          }
        >
          {sensorProfilesQuery.isError ? (
            <EmptyState
              title="传感器模板加载失败"
              description={sensorProfilesQuery.error.message}
            />
          ) : sensorProfiles.length === 0 ? (
            <EmptyState title="还没有模板" description="先创建一个和车型绑定的传感器模板。" />
          ) : (
            <div className="flex flex-col gap-3">
              {sensorProfiles.map((profile) => (
                <button
                  key={profile.profile_name}
                  className={[
                    'rounded-[18px] border p-4 text-left transition',
                    selectedProfileName === profile.profile_name
                      ? 'border-brand-200 bg-brand-50/70'
                      : 'border-secondaryGray-200 bg-secondaryGray-50/60 hover:-translate-y-0.5 hover:shadow-card'
                  ].join(' ')}
                  onClick={() => selectProfile(profile)}
                  type="button"
                >
                  <strong className="block text-sm font-extrabold text-navy-900">
                    {profile.display_name}
                  </strong>
                  <p className="mt-2 text-xs leading-5 text-secondaryGray-600">
                    {profile.vehicle_model ?? '未绑定车型'}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2 text-[11px] font-semibold text-secondaryGray-600">
                    <span className="rounded-full bg-white px-3 py-1">{profile.profile_name}</span>
                    <span className="rounded-full bg-white px-3 py-1">
                      {profile.sensors.length} sensors
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel
            title="模板编辑"
            subtitle="坐标、姿态、分辨率和高级属性都在这里维护。保存后场景页会直接复用。"
            actions={
              <button
                className="horizon-button"
                disabled={saveMutation.isPending}
                onClick={() => saveMutation.mutate()}
                type="button"
              >
                {saveMutation.isPending ? '保存中...' : editor.is_new ? '创建模板' : '保存模板'}
              </button>
            }
          >
            <div className="form-grid">
              <label className="field">
                <span>模板标识</span>
                <input
                  onChange={(event) => updateEditor('profile_name', event.target.value)}
                  placeholder="vehicle_sedan_alpha"
                  value={editor.profile_name}
                />
              </label>

              <label className="field">
                <span>显示名称</span>
                <input
                  onChange={(event) => updateEditor('display_name', event.target.value)}
                  placeholder="Sedan Alpha"
                  value={editor.display_name}
                />
              </label>

              <label className="field">
                <span>车型蓝图</span>
                <input
                  onChange={(event) => updateEditor('vehicle_model', event.target.value)}
                  placeholder="vehicle.lincoln.mkz_2017"
                  value={editor.vehicle_model}
                />
              </label>

              <label className="field">
                <span>描述</span>
                <input
                  onChange={(event) => updateEditor('description', event.target.value)}
                  placeholder="该车型的默认前向采集模板"
                  value={editor.description}
                />
              </label>
            </div>

            <label className="field mt-4">
              <span>扩展元数据 JSON</span>
              <textarea
                className="min-h-[120px]"
                onChange={(event) => updateEditor('metadata_text', event.target.value)}
                value={editor.metadata_text}
              />
            </label>

            <div className="mt-5 flex flex-wrap gap-3">
              <button className="horizon-button-secondary" onClick={() => addSensor('sensor.camera.rgb')} type="button">
                添加 RGB 相机
              </button>
              <button className="horizon-button-secondary" onClick={() => addSensor('sensor.lidar.ray_cast')} type="button">
                添加 LiDAR
              </button>
              <button className="horizon-button-secondary" onClick={() => addSensor('sensor.other.radar')} type="button">
                添加 Radar
              </button>
            </div>

            <div className="mt-5 flex flex-col gap-4">
              {editor.sensors.map((sensor, index) => (
                <section
                  key={`${sensor.id || 'sensor'}-${index}`}
                  className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/60 p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <strong className="block text-sm font-extrabold text-navy-900">
                        传感器 {index + 1}
                      </strong>
                      <p className="mt-1 text-xs text-secondaryGray-600">
                        建议按车型固定相对坐标，场景运行时只选模板名。
                      </p>
                    </div>
                    <button
                      className="text-sm font-semibold text-rose-500"
                      disabled={editor.sensors.length <= 1}
                      onClick={() => removeSensor(index)}
                      type="button"
                    >
                      删除
                    </button>
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <label className="field">
                      <span>ID</span>
                      <input
                        onChange={(event) =>
                          updateSensor(index, (current) => ({ ...current, id: event.target.value }))
                        }
                        value={sensor.id}
                      />
                    </label>

                    <label className="field">
                      <span>类型</span>
                      <input
                        onChange={(event) =>
                          updateSensor(index, (current) => ({ ...current, type: event.target.value }))
                        }
                        value={sensor.type}
                      />
                    </label>
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    {SENSOR_NUMBER_FIELDS.map((field) => (
                      <label key={field.key} className="field">
                        <span>{field.label}</span>
                        <input
                          min={field.min}
                          onChange={(event) =>
                            updateSensor(index, (current) => ({
                              ...current,
                              [field.key]: parseOptionalNumber(event.target.value)
                            }))
                          }
                          step={field.step}
                          type="number"
                          value={
                            typeof sensor[field.key] === 'number' ? `${sensor[field.key]}` : ''
                          }
                        />
                      </label>
                    ))}
                  </div>

                  <label className="field mt-4">
                    <span>高级属性 JSON</span>
                    <textarea
                      className="min-h-[110px]"
                      onChange={(event) =>
                        updateSensor(index, (current) => ({
                          ...current,
                          attributes_text: event.target.value
                        }))
                      }
                      value={sensor.attributes_text}
                    />
                  </label>
                </section>
              ))}
            </div>

            {saveMutation.error ? (
              <p className="mt-4 text-sm text-rose-500">{saveMutation.error.message}</p>
            ) : null}
            {saveMutation.data ? (
              <p className="mt-4 text-sm text-emerald-400">
                已保存模板 {saveMutation.data.display_name}，场景页会在刷新后使用最新参数。
              </p>
            ) : null}
          </Panel>

          <div className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <Panel title="当前保存态" subtitle="便于对照 YAML 文件和最近一次保存结果。">
              {selectedProfile ? (
                <pre className="json-block json-block--compact">{selectedProfile.raw_yaml}</pre>
              ) : (
                <EmptyState title="还没有已保存模板" description="先选择或创建一个传感器模板。" />
              )}
            </Panel>

            <Panel title="待保存预览" subtitle="这里展示的是即将发给后端的 payload。">
              <JsonBlock compact value={previewPayload} />
            </Panel>
          </div>

          <Panel title="模板使用范围" subtitle="方便确认哪些场景会引用当前模板。">
            {selectedProfileName ? (
              selectedProfileScenarioDefaults.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {selectedProfileScenarioDefaults.map((item: ScenarioCatalogItem) => (
                    <span
                      key={item.scenario_id}
                      className="rounded-full bg-secondaryGray-50 px-3 py-2 text-xs font-semibold text-secondaryGray-600"
                    >
                      {item.display_name}
                    </span>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="当前没有默认绑定场景"
                  description="不过支持传感器模板切换的场景依然可以在场景页里选用它。"
                />
              )
            ) : (
              <EmptyState title="未选择模板" description="先从左侧选择一个模板。" />
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
