import { useState } from 'react';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { listGateways } from '../../api/gateways';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, sortByActivity } from '../../lib/format';

export function GatewaysPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');

  const gatewaysQuery = useQuery({
    queryKey: ['gateways'],
    queryFn: listGateways,
    refetchInterval: 5000
  });

  const gateways = sortByActivity(gatewaysQuery.data ?? []);
  const readyCount = gateways.filter((gateway) => gateway.status === 'READY').length;
  const busyCount = gateways.filter((gateway) => gateway.status === 'BUSY').length;
  const errorCount = gateways.filter((gateway) => gateway.status === 'ERROR').length;
  const latestHeartbeat = gateways[0]?.last_heartbeat_at_utc ?? null;
  const filteredGateways = gateways.filter((gateway) => {
    const statusMatched = !statusFilter || gateway.status === statusFilter;
    const keyword = searchKeyword.trim().toLowerCase();
    const searchMatched =
      !keyword ||
      gateway.gateway_id.toLowerCase().includes(keyword) ||
      gateway.name.toLowerCase().includes(keyword) ||
      String(gateway.address ?? '').toLowerCase().includes(keyword);
    return statusMatched && searchMatched;
  });

  return (
    <div className="page-stack">
      <PageHeader
        title="Gateways"
        description="树莓派网关详情集中展示，先解决 HDMI 输入、存储和心跳问题，再谈 DUT 接入。"
        actions={
          <button className="horizon-button-secondary" onClick={() => void queryClient.invalidateQueries({ queryKey: ['gateways'] })} type="button">
            刷新网关
          </button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="teal" label="READY" value={readyCount} hint="可用于 capture / run 绑定" />
        <MetricCard accent="orange" label="BUSY" value={busyCount} hint="当前正在执行任务" />
        <MetricCard accent="rose" label="ERROR" value={errorCount} hint="优先检查 HDMI / UDC / disk" />
        <MetricCard accent="blue" label="Latest Heartbeat" value={latestHeartbeat ? formatDateTime(latestHeartbeat) : '-'} hint="最近心跳时间" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_320px]">
        <Panel title="网关列表">
          {filteredGateways.length === 0 ? (
            <EmptyState title="没有匹配网关" description="当前还没有注册中的 Pi gateway，或者筛选条件过严。" />
          ) : (
            <div className="flex flex-col gap-4">
              {filteredGateways.map((gateway) => (
                <div key={gateway.gateway_id} className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/60 p-5 shadow-card">
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <StatusPill status={gateway.status} />
                        <span className="text-sm font-bold text-brand-600">{gateway.gateway_id}</span>
                      </div>
                      <strong className="mt-3 block text-xl font-extrabold tracking-[-0.03em] text-navy-900">{gateway.name}</strong>
                      <p className="mt-1 text-sm text-secondaryGray-600">{gateway.address ?? '无地址回传'}</p>
                    </div>
                    <Link className="horizon-button" to={`/gateways/${gateway.gateway_id}`}>
                      详情
                    </Link>
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Capture</span>
                      <strong className="mt-2 block text-sm text-navy-900">
                        {String(gateway.metrics.capture_resolution ?? gateway.metrics.hdmi_detected_format ?? '-')}
                      </strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">UDC</span>
                      <strong className="mt-2 block text-sm text-navy-900">{String(gateway.metrics.udc_state ?? '-')}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Heartbeat</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatDateTime(gateway.last_heartbeat_at_utc)}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Current Run</span>
                      <strong className="mt-2 block break-all text-sm text-navy-900">{gateway.current_run_id ?? '-'}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="筛选器">
          <div className="form-grid">
            <label className="field">
              <span>状态</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">全部</option>
                {['READY', 'BUSY', 'ERROR', 'UNKNOWN', 'OFFLINE'].map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>关键字</span>
              <input
                placeholder="gateway_id / 名称 / 地址"
                value={searchKeyword}
                onChange={(event) => setSearchKeyword(event.target.value)}
              />
            </label>
          </div>
          <div className="mt-5 rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
            <span className="block text-[11px] font-extrabold uppercase tracking-[0.18em] text-secondaryGray-500">Focus</span>
            <p className="mt-3 text-sm leading-6 text-secondaryGray-600">
              READY 网关优先用于采集验证。ERROR 状态优先检查 `hdmi_detected_format`、`udc_state`、磁盘路径和最近心跳。
            </p>
          </div>
        </Panel>
      </div>
    </div>
  );
}
