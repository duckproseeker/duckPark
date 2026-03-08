import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';

import { listCaptures } from '../../api/captures';
import { getGateway } from '../../api/gateways';
import { EmptyState } from '../../components/common/EmptyState';
import { JsonBlock } from '../../components/common/JsonBlock';
import { KeyValueGrid } from '../../components/common/KeyValueGrid';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { ProgressBar } from '../../components/common/ProgressBar';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime } from '../../lib/format';
import {
  deriveGatewayFrameDropRate,
  deriveGatewayInputFps,
  deriveGatewayLatencyMs,
  deriveGatewayOutputFps,
  deriveGatewayPowerW,
  deriveGatewayTemperatureC,
  formatMetric
} from '../../lib/platform';

export function DeviceDetailPage() {
  const { gatewayId = '' } = useParams();

  const gatewayQuery = useQuery({
    queryKey: ['gateways', gatewayId],
    queryFn: () => getGateway(gatewayId),
    enabled: Boolean(gatewayId),
    refetchInterval: 5000
  });

  const capturesQuery = useQuery({
    queryKey: ['captures', gatewayId],
    queryFn: () => listCaptures({ gatewayId }),
    enabled: Boolean(gatewayId),
    refetchInterval: 5000
  });

  const gateway = gatewayQuery.data;
  const captures = capturesQuery.data ?? [];

  if (!gatewayId) {
    return <EmptyState title="缺少设备 ID" description="路由参数里没有 gateway_id。" />;
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="设备详情"
        eyebrow="Devices / Detail"
        chips={['设备遥测', '采集证据链', '底层诊断']}
        description={gateway ? `${gateway.name} / ${gateway.gateway_id}` : gatewayId}
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="horizon-button-secondary" to="/devices">
              返回设备中心
            </Link>
            <Link className="horizon-button" to="/reports">
              查看报告中心
            </Link>
          </div>
        }
      />

      {!gateway ? (
        <Panel>
          <p>加载中...</p>
        </Panel>
      ) : (
        <>
          <Panel title="基础信息">
            <KeyValueGrid
              items={[
                { label: '状态', value: <StatusPill status={gateway.status} /> },
                { label: '名称', value: gateway.name },
                { label: '设备 ID', value: gateway.gateway_id },
                { label: '地址', value: gateway.address ?? '-' },
                { label: '当前执行', value: gateway.current_run_id ?? '-' },
                { label: '最近心跳', value: formatDateTime(gateway.last_heartbeat_at_utc) },
                { label: '最近看到', value: formatDateTime(gateway.last_seen_at_utc) },
                { label: 'Agent 版本', value: gateway.agent_version ?? '-' }
              ]}
            />
          </Panel>

          <div className="grid gap-5 2xl:grid-cols-[minmax(0,1.3fr)_420px]">
            <div className="flex flex-col gap-5">
              <Panel title="关键遥测">
                <KeyValueGrid
                  items={[
                    { label: '输入 FPS', value: formatMetric(deriveGatewayInputFps(gateway), 1) },
                    { label: '输出 FPS', value: formatMetric(deriveGatewayOutputFps(gateway), 1) },
                    { label: '平均延迟', value: formatMetric(deriveGatewayLatencyMs(gateway), 1, ' ms') },
                    { label: '丢帧率', value: formatMetric(deriveGatewayFrameDropRate(gateway), 3) },
                    { label: '功耗', value: formatMetric(deriveGatewayPowerW(gateway), 1, ' W') },
                    { label: '温度', value: formatMetric(deriveGatewayTemperatureC(gateway), 1, '°C') },
                    { label: 'HDMI 检测格式', value: String(gateway.metrics.hdmi_detected_format ?? '-') },
                    { label: '采集分辨率', value: String(gateway.metrics.capture_resolution ?? '-') },
                    { label: 'UDC 状态', value: String(gateway.metrics.udc_state ?? '-') },
                    { label: '最近错误', value: String(gateway.metrics.last_error ?? '-') }
                  ]}
                />
              </Panel>

              <Panel title="采集记录">
                {captures.length === 0 ? (
                  <EmptyState title="没有采集记录" description="该设备当前没有关联 capture 记录。" />
                ) : (
                  <div className="flex flex-col gap-4">
                    {captures.map((capture) => (
                      <div key={capture.capture_id} className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                        <div className="flex items-center justify-between gap-3">
                          <div className="min-w-0">
                            <strong className="block truncate text-sm font-bold text-navy-900">{capture.capture_id}</strong>
                            <p className="mt-1 truncate text-xs text-secondaryGray-500">{capture.save_dir}</p>
                          </div>
                          <StatusPill status={capture.status} />
                        </div>
                        <div className="mt-3">
                          <ProgressBar
                            label={`${capture.saved_frames}/${capture.max_frames ?? 0}`}
                            max={capture.max_frames ?? Math.max(capture.saved_frames, 1)}
                            value={capture.saved_frames}
                          />
                        </div>
                        <p className="mt-3 text-xs text-secondaryGray-500">{formatDateTime(capture.updated_at_utc)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </Panel>
            </div>

            <div className="flex flex-col gap-5">
              <Panel title="能力声明">
                <JsonBlock value={gateway.capabilities} />
              </Panel>

              <Panel title="原始 metrics">
                <JsonBlock compact value={gateway.metrics} />
              </Panel>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
