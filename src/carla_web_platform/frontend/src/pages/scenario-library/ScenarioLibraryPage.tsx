import { useState } from 'react';

import { useQuery } from '@tanstack/react-query';

import { listScenarioCatalog } from '../../api/scenarios';
import { EmptyState } from '../../components/common/EmptyState';
import { JsonBlock } from '../../components/common/JsonBlock';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';

export function ScenarioLibraryPage() {
  const catalogQuery = useQuery({ queryKey: ['scenario-catalog'], queryFn: listScenarioCatalog });
  const [supportFilter, setSupportFilter] = useState<'all' | 'native' | 'catalog_only'>('all');
  const [selectedScenarioId, setSelectedScenarioId] = useState('');

  const catalogItems = catalogQuery.data ?? [];
  const nativeCount = catalogItems.filter((item) => item.execution_support === 'native').length;
  const officialCount = catalogItems.filter((item) => item.execution_support === 'catalog_only').length;
  const filteredItems = catalogItems.filter((item) =>
    supportFilter === 'all' ? true : item.execution_support === supportFilter
  );
  const selectedItem =
    filteredItems.find((item) => item.scenario_id === selectedScenarioId) ?? filteredItems[0] ?? null;

  return (
    <div className="page-stack">
      <PageHeader
        title="Scenario Library"
        description="官方 ScenarioRunner 模板和本地可执行场景分开管理。当前 catalog_only 代表模板已导入，但还没有本地 executor 适配实现。"
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="blue" label="Catalog Items" value={catalogItems.length} hint="场景库总条目数" />
        <MetricCard accent="teal" label="Native" value={nativeCount} hint="可直接由本地 executor 执行" />
        <MetricCard accent="violet" label="Catalog Only" value={officialCount} hint="官方模板已导入但未适配执行器" />
        <MetricCard accent="orange" label="Selected Support" value={supportFilter.toUpperCase()} hint="当前筛选模式" />
      </div>

      <div className="grid gap-5 2xl:grid-cols-[minmax(0,1.35fr)_420px]">
        <Panel title="Scenario Catalog" subtitle="优先把 native 场景跑通；official 模板先用于场景管理和参数设计。">
          <div className="mb-4 flex flex-wrap gap-3">
            {[
              { label: 'ALL', value: 'all' as const },
              { label: 'NATIVE', value: 'native' as const },
              { label: 'CATALOG_ONLY', value: 'catalog_only' as const }
            ].map((item) => (
              <button
                key={item.value}
                className={[
                  'rounded-full px-4 py-2 text-sm font-bold transition',
                  supportFilter === item.value
                    ? 'bg-brand-500 text-white shadow-glow'
                    : 'bg-secondaryGray-50 text-secondaryGray-600'
                ].join(' ')}
                onClick={() => setSupportFilter(item.value)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>

          {filteredItems.length === 0 ? (
            <EmptyState title="没有匹配场景" description="当前筛选条件下没有找到场景条目。" />
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {filteredItems.map((item) => (
                <button
                  key={item.scenario_id}
                  className={[
                    'rounded-[24px] border p-5 text-left transition',
                    selectedItem?.scenario_id === item.scenario_id
                      ? 'border-brand-200 bg-brand-50/70 shadow-card'
                      : 'border-secondaryGray-200 bg-secondaryGray-50/60 hover:-translate-y-0.5 hover:shadow-card'
                  ].join(' ')}
                  onClick={() => setSelectedScenarioId(item.scenario_id)}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <strong className="block text-lg font-extrabold tracking-[-0.03em] text-navy-900">
                        {item.display_name}
                      </strong>
                      <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{item.description}</p>
                    </div>
                    <StatusPill status={item.execution_support === 'native' ? 'READY' : 'CATALOG'} />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold text-secondaryGray-500">
                    <span className="rounded-full bg-white px-3 py-1">{item.default_map_name}</span>
                    <span className="rounded-full bg-white px-3 py-1">{item.source.provider}</span>
                    {item.source.source_file && <span className="rounded-full bg-white px-3 py-1">{item.source.source_file}</span>}
                  </div>
                </button>
              ))}
            </div>
          )}
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel title="Template Preview" subtitle="用来核对默认地图、天气和传感器块结构。">
            {selectedItem ? (
              <JsonBlock compact value={selectedItem.descriptor_template} />
            ) : (
              <EmptyState title="未选择场景" description="从左侧选择一个场景条目。" />
            )}
          </Panel>

          <Panel title="Source Metadata" subtitle="官方模板来源和当前执行支持状态。">
            {selectedItem ? (
              <JsonBlock
                compact
                value={{
                  scenario_id: selectedItem.scenario_id,
                  execution_support: selectedItem.execution_support,
                  source: selectedItem.source
                }}
              />
            ) : (
              <EmptyState title="没有源信息" description="先选择场景条目。" />
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
