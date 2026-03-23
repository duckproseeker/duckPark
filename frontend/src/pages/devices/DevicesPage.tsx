import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { getDevicesWorkspace } from '../../api/devices';
import { EmptyState } from '../../components/common/EmptyState';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';
import { TelemetryDashboard } from '../../components/common/TelemetryDashboard';
import { sortByActivity } from '../../lib/format';

export function DevicesPage() {
  const workspaceQuery = useQuery({
    queryKey: ['devices', 'workspace'],
    queryFn: getDevicesWorkspace,
    refetchInterval: 5000
  });

  const gateways = sortByActivity(workspaceQuery.data?.gateways ?? []);
  const tasks = sortByActivity(workspaceQuery.data?.benchmark_tasks ?? []);

  return (
    <div className="page-stack">
      <PageHeader
        title="单 DUT 运行观测"
        eyebrow="DUT Observatory"
        chips={['硬件遥测', '时间序列趋势', '中性观测']}
        description="查看设备状态和遥测趋势。"
      />

      <div className="grid gap-5">
        {workspaceQuery.isLoading ? (
          <EmptyState title="观测台加载中" description="正在读取设备状态。" />
        ) : workspaceQuery.isError ? (
          <EmptyState
            title="观测台加载失败"
            description={workspaceQuery.error instanceof Error ? workspaceQuery.error.message : '接口异常。'}
          />
        ) : gateways.length === 0 ? (
          <EmptyState title="没有连入的设备" description="当前没有处于观测中的待测芯片网关。" />
        ) : (
          <div className="flex flex-col gap-6">
            {gateways.map((gateway) => {
              const activeTask = tasks.find(
                (t) => t.hil_config?.gateway_id === gateway.gateway_id && ['RUNNING', 'STARTING', 'CREATED'].includes(t.status)
              );

              return (
                <Panel key={gateway.gateway_id} title={`观测节点: ${gateway.name}`} subtitle="运行状态与遥测">
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between mb-6 border-b border-secondaryGray-200/50 dark:border-slate-700/50 pb-6">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <StatusPill status={gateway.status} />
                        <span className="rounded-full bg-white dark:bg-slate-800 border border-secondaryGray-200 dark:border-slate-700 px-3 py-1 text-xs font-semibold text-secondaryGray-600 dark:text-slate-300">
                          网关: {gateway.gateway_id}
                        </span>
                      </div>
                      {gateway.status_detail ? (
                        <p className="mt-3 text-sm text-secondaryGray-500 dark:text-slate-400">
                          {gateway.status_detail}
                        </p>
                      ) : null}

                      <div className="mt-4 flex flex-col gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-secondaryGray-500 dark:text-slate-400 w-20">DUT 型号:</span>
                          <span className="text-sm font-extrabold text-navy-900 dark:text-slate-100">
                            {gateway.metrics?.dut_model_name ? String(gateway.metrics.dut_model_name) : '未登记'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-secondaryGray-500 dark:text-slate-400 w-20">当前任务:</span>
                          {activeTask ? (
                            <span className="text-sm text-navy-900 dark:text-slate-100">
                              {activeTask.benchmark_name} <span className="text-secondaryGray-400 dark:text-slate-500">({activeTask.status})</span>
                            </span>
                          ) : (
                            <span className="text-sm text-secondaryGray-400 dark:text-slate-500">无运行中的测试</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <Link className="horizon-button" to={`/devices/${gateway.gateway_id}`}>
                      追踪完整日志
                    </Link>
                  </div>

                  <TelemetryDashboard
                    deviceMetrics={gateway.metrics}
                    runActive={['READY', 'BUSY'].includes(gateway.status)}
                    sampleTimestampUtc={gateway.last_heartbeat_at_utc}
                  />
                </Panel>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
