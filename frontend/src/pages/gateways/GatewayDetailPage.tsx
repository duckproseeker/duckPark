import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';

import { getGateway } from '../../api/gateways';
import { EmptyState } from '../../components/common/EmptyState';
import { JsonBlock } from '../../components/common/JsonBlock';
import { KeyValueGrid } from '../../components/common/KeyValueGrid';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime } from '../../lib/format';

export function GatewayDetailPage() {
  const { gatewayId = '' } = useParams();
  const gatewayQuery = useQuery({
    queryKey: ['gateways', gatewayId],
    queryFn: () => getGateway(gatewayId),
    enabled: Boolean(gatewayId),
    refetchInterval: 5000
  });

  const gateway = gatewayQuery.data;
  if (!gatewayId) {
    return <EmptyState title="缺少 gateway_id" description="路由参数里没有 gateway_id。" />;
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Gateway Detail"
        description={gateway ? `${gateway.name} / ${gateway.gateway_id}` : gatewayId}
        actions={
          <div className="button-row">
            <Link className="button button--secondary" to="/gateways">
              返回列表
            </Link>
            <Link className="button" to="/captures">
              打开采集列表
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
                { label: '网关 ID', value: gateway.gateway_id },
                { label: '地址', value: gateway.address ?? '-' },
                { label: '当前运行', value: gateway.current_run_id ?? '-' },
                { label: '最近心跳', value: formatDateTime(gateway.last_heartbeat_at_utc) },
                { label: '最近看到', value: formatDateTime(gateway.last_seen_at_utc) },
                { label: 'Agent 版本', value: gateway.agent_version ?? '-' }
              ]}
            />
          </Panel>

          <div className="two-column-grid">
            <Panel title="关键指标">
              <KeyValueGrid
                items={[
                  { label: 'HDMI 检测格式', value: String(gateway.metrics.hdmi_detected_format ?? '-') },
                  { label: '采集分辨率', value: String(gateway.metrics.capture_resolution ?? '-') },
                  { label: 'TMDS 检测', value: String(gateway.metrics.hdmi_tmds_signal_detected ?? '-') },
                  { label: '稳定同步', value: String(gateway.metrics.hdmi_stable_sync_signal ?? '-') },
                  { label: 'UDC 状态', value: String(gateway.metrics.udc_state ?? '-') },
                  { label: '活跃采集', value: String(gateway.metrics.active_capture_id ?? '-') },
                  { label: '最近保存帧数', value: String(gateway.metrics.saved_frames ?? '-') },
                  { label: '最近错误', value: String(gateway.metrics.last_error ?? '-') }
                ]}
              />
            </Panel>

            <Panel title="能力声明">
              <JsonBlock value={gateway.capabilities} />
            </Panel>
          </div>

          <Panel title="完整 metrics">
            <JsonBlock value={gateway.metrics} />
          </Panel>
        </>
      )}
    </div>
  );
}
