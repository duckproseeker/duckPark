import { useEffect, useMemo, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { listEnvironmentPresets, listMaps, listScenarioCatalog, listSensorProfiles } from '../../api/scenarios';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { MultiSelectDropdown } from '../../components/common/MultiSelectDropdown';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';

export function ScenarioSetsPage() {
  const catalogQuery = useQuery({ queryKey: ['scenario-catalog'], queryFn: listScenarioCatalog });
  const environmentQuery = useQuery({ queryKey: ['environment-presets'], queryFn: listEnvironmentPresets });
  const sensorProfilesQuery = useQuery({ queryKey: ['sensor-profiles'], queryFn: listSensorProfiles });
  const mapsQuery = useQuery({ queryKey: ['maps'], queryFn: listMaps });

  const nativeScenarios = (catalogQuery.data ?? []).filter((item) => item.execution_support === 'native');
  const environmentPresets = environmentQuery.data ?? [];
  const sensorProfiles = sensorProfilesQuery.data ?? [];
  const maps = mapsQuery.data ?? [];

  const [scenarioIds, setScenarioIds] = useState<string[]>([]);
  const [mapNames, setMapNames] = useState<string[]>([]);
  const [environmentIds, setEnvironmentIds] = useState<string[]>([]);
  const [sensorNames, setSensorNames] = useState<string[]>([]);

  useEffect(() => {
    if (scenarioIds.length === 0 && nativeScenarios[0]) {
      setScenarioIds([nativeScenarios[0].scenario_id]);
    }
  }, [nativeScenarios, scenarioIds.length]);

  useEffect(() => {
    if (mapNames.length === 0 && maps[0]) {
      setMapNames([maps[0].map_name]);
    }
  }, [maps, mapNames.length]);

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

  const previewRows = useMemo(() => {
    const selectedScenarios = nativeScenarios.filter((item) => scenarioIds.includes(item.scenario_id));
    const selectedMaps = maps.filter((item) => mapNames.includes(item.map_name));
    const selectedEnvironments = environmentPresets.filter((item) => environmentIds.includes(item.preset_id));
    const selectedSensors = sensorProfiles.filter((item) => sensorNames.includes(item.profile_name));

    const rows: Array<{ scenario: string; map: string; environment: string; sensor: string }> = [];
    for (const scenario of selectedScenarios) {
      for (const map of selectedMaps) {
        for (const environment of selectedEnvironments) {
          for (const sensor of selectedSensors) {
            rows.push({
              scenario: scenario.display_name,
              map: map.display_name,
              environment: environment.display_name,
              sensor: sensor.display_name
            });
          }
        }
      }
    }
    return rows;
  }, [environmentIds, environmentPresets, mapNames, maps, nativeScenarios, scenarioIds, sensorNames, sensorProfiles]);

  return (
    <div className="page-stack">
      <PageHeader
        title="场景集"
        eyebrow="Scenario Sets / Matrices"
        chips={['场景矩阵', '组合规划', '多地图多天气']}
        description="场景集页负责规划组合空间，不直接保存业务实体。你在这里确认场景、地图、天气和传感器组合，再去执行中心把组合展开成批量 runs。"
        actions={
          <Link className="horizon-button" to="/executions">
            用这些组合发起执行
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="blue" label="Native 场景" value={nativeScenarios.length} hint="当前可直接执行的场景模板" />
        <MetricCard accent="violet" label="地图" value={maps.length} hint="来自 CARLA server 的可用地图" />
        <MetricCard accent="teal" label="天气预设" value={environmentPresets.length} hint="运行前与运行中都能复用" />
        <MetricCard accent="orange" label="组合数" value={previewRows.length} hint="基于当前勾选的矩阵展开数" />
      </div>

      <div className="grid gap-5 2xl:grid-cols-[minmax(0,1.55fr)_420px]">
        <Panel title="组合选择器" subtitle="用下拉选择器规划场景矩阵，避免把所有场景、地图和天气直接堆在页面上。">
          {nativeScenarios.length === 0 ? (
            <EmptyState title="没有 native 场景" description="后端尚未返回可直接执行的场景目录。" />
          ) : (
            <div className="grid gap-4 xl:grid-cols-2">
              <MultiSelectDropdown
                label="场景池"
                helperText="优先选择 native 场景中的核心回归场景"
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
                helperText="UI 只显示归一化后的地图名称，后端统一使用 Opt 版本"
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
                helperText="建议先选 1-2 种代表性天气，逐步扩展矩阵"
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
                helperText="明确输入模式，避免同一批任务混入多套采集配置"
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
          )}
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel title="矩阵摘要" subtitle="组合越多，执行和报告成本越高。">
            <div className="grid gap-3">
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">已选场景</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{scenarioIds.length}</strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">已选地图</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{mapNames.length}</strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">已选天气</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{environmentIds.length}</strong>
              </div>
              <div className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                <span className="block text-sm text-secondaryGray-500">已选传感器模板</span>
                <strong className="mt-2 block text-2xl font-extrabold tracking-[-0.04em] text-navy-900">{sensorNames.length}</strong>
              </div>
            </div>
          </Panel>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_420px]">
        <Panel title="组合预览" subtitle="这里只展示矩阵展开结果，不会直接向后端写入。">
          {previewRows.length === 0 ? (
            <EmptyState title="没有组合" description="至少选择 1 个场景、1 张地图、1 个天气和 1 个传感器模板。" />
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {previewRows.slice(0, 12).map((row, index) => (
                <div key={`${row.scenario}-${row.map}-${row.environment}-${row.sensor}-${index}`} className="rounded-[18px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <strong className="text-sm font-bold text-navy-900">{row.scenario}</strong>
                    <StatusPill status="READY" />
                  </div>
                  <p className="mt-2 text-sm text-secondaryGray-600">{row.map}</p>
                  <p className="mt-1 text-xs text-secondaryGray-500">{row.environment}</p>
                  <p className="mt-1 text-xs text-secondaryGray-500">{row.sensor}</p>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="使用建议" subtitle="场景集页只负责规划，不负责执行。">
          <div className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4 text-sm leading-6 text-secondaryGray-600">
            <p>1. 先用 1 个场景、1 张地图、1 个天气、1 个传感器模板跑通链路。</p>
            <p>2. 再逐步扩大到多地图、多天气矩阵。</p>
            <p>3. 如果组合数超过 24，建议拆成多个基准任务分批执行。</p>
            <p>4. 真正的批量创建和自动展开在执行中心完成。</p>
          </div>
        </Panel>
      </div>
    </div>
  );
}
