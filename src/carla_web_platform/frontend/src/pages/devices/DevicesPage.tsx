import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { getDevicesWorkspace } from '../../api/devices';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { ProgressBar } from '../../components/common/ProgressBar';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, sortByActivity } from '../../lib/format';
import {
  average,
  deriveGatewayFrameDropRate,
  deriveGatewayInputFps,
  deriveGatewayOutputFps,
  deriveGatewayPowerW,
  deriveGatewayTemperatureC,
  formatMetric
} from '../../lib/platform';

export function DevicesPage() {
  const workspaceQuery = useQuery({
    queryKey: ['devices', 'workspace'],
    queryFn: getDevicesWorkspace,
    refetchInterval: 5000
  });

  const gateways = sortByActivity(workspaceQuery.data?.gateways ?? []);
  const captures = sortByActivity(workspaceQuery.data?.captures ?? []);
  const tasks = sortByActivity(workspaceQuery.data?.benchmark_tasks ?? []);
  const summary = workspaceQuery.data?.summary;
  const onlineDevices = summary?.online_device_count ?? 0;
  const runningCaptures = summary?.running_capture_count ?? 0;
  const avgInputFps = summary?.avg_input_fps ?? average(gateways.map(deriveGatewayInputFps));
  const avgOutputFps = summary?.avg_output_fps ?? average(gateways.map(deriveGatewayOutputFps));
  const avgDropRate = summary?.avg_frame_drop_rate ?? average(gateways.map(deriveGatewayFrameDropRate));
  const avgPower = summary?.avg_power_w ?? average(gateways.map(deriveGatewayPowerW));
  const avgTemperature =
    summary?.avg_temperature_c ?? average(gateways.map(deriveGatewayTemperatureC));

  return (
    <div className="page-stack">
      <PageHeader
        title="设备中心"
        eyebrow="Devices / Ops"
        chips={['底层能力', '设备遥测', '采集链路']}
        description="设备中心下沉承接网关、采集和运维视角。它是测评平台的底层实现区域，不再主导业务主导航。"
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <MetricCard accent="blue" label="在线设备" value={onlineDevices} hint="READY / BUSY 网关" />
        <MetricCard accent="teal" label="运行中采集" value={runningCaptures} hint="当前仍在保存帧的 capture" />
        <MetricCard accent="violet" label="输入 FPS" value={formatMetric(avgInputFps, 1)} hint="来自网关 metrics.input_fps" />
        <MetricCard accent="orange" label="输出 FPS" value={formatMetric(avgOutputFps, 1)} hint="来自网关 metrics.output_fps" />
        <MetricCard accent="rose" label="平均功耗" value={formatMetric(avgPower, 1, ' W')} hint="未接入则显示待接入" />
        <MetricCard accent="orange" label="平均温度" value={formatMetric(avgTemperature, 1, '°C')} hint="未接入则显示待接入" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_420px]">
        <Panel title="设备列表" subtitle="设备页只负责确认底层链路是否稳定，不再承担项目与报告语义。">
          {workspaceQuery.isLoading ? (
            <EmptyState title="设备工作台加载中" description="正在同步设备、采集和任务上下文。" />
          ) : workspaceQuery.isError ? (
            <EmptyState
              title="设备工作台加载失败"
              description={workspaceQuery.error instanceof Error ? workspaceQuery.error.message : '设备工作台接口异常。'}
            />
          ) : gateways.length === 0 ? (
            <EmptyState title="没有设备" description="当前还没有注册中的 Pi gateway。" />
          ) : (
            <div className="flex flex-col gap-4">
              {gateways.map((gateway) => (
                <div key={gateway.gateway_id} className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/60 p-5 shadow-card">
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <StatusPill status={gateway.status} />
                        <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-secondaryGray-600">
                          {gateway.gateway_id}
                        </span>
                      </div>
                      <strong className="mt-3 block text-xl font-extrabold tracking-[-0.03em] text-navy-900">{gateway.name}</strong>
                      <p className="mt-1 text-sm text-secondaryGray-600">{gateway.address ?? '无地址回传'}</p>
                    </div>
                    <Link className="horizon-button" to={`/devices/${gateway.gateway_id}`}>
                      查看设备详情
                    </Link>
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">输入 FPS</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatMetric(deriveGatewayInputFps(gateway), 1)}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">输出 FPS</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatMetric(deriveGatewayOutputFps(gateway), 1)}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">丢帧率</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatMetric(deriveGatewayFrameDropRate(gateway), 3)}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">功耗</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatMetric(deriveGatewayPowerW(gateway), 1, ' W')}</strong>
                    </div>
                    <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                      <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">温度</span>
                      <strong className="mt-2 block text-sm text-navy-900">{formatMetric(deriveGatewayTemperatureC(gateway), 1, '°C')}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel title="采集链路" subtitle="采集是运维视角的证据链，不是主业务入口。">
            {captures.length === 0 ? (
              <EmptyState title="没有采集记录" description="当前还没有 capture 任务。" />
            ) : (
              <div className="flex flex-col gap-4">
                {captures.slice(0, 8).map((capture) => (
                  <div key={capture.capture_id} className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <strong className="block truncate text-sm font-bold text-navy-900">{capture.gateway_id}</strong>
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

          <Panel title="运维提示">
            <div className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4 text-sm leading-6 text-secondaryGray-600">
              <p>1. 设备中心优先关注 HDMI、UVC、心跳和保存帧数。</p>
              <p>2. 如果输入/输出 FPS、温度、功耗未回传，前端会明确显示待接入。</p>
              <p>3. DUT 型号属于接入与运维登记信息，应在创建任务时和设备绑定一起录入。</p>
              <p>4. 设备稳定后，再回执行中心和报告中心处理测评闭环。</p>
            </div>
          </Panel>
        </div>
      </div>

      <Panel title="设备群概览" subtitle="辅助看当前设备侧的波动和告警。">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/70 p-5">
            <span className="block text-sm text-secondaryGray-500">平均输入 FPS</span>
            <strong className="mt-2 block text-3xl font-extrabold tracking-[-0.04em] text-navy-900">{formatMetric(avgInputFps, 1)}</strong>
          </div>
          <div className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/70 p-5">
            <span className="block text-sm text-secondaryGray-500">平均输出 FPS</span>
            <strong className="mt-2 block text-3xl font-extrabold tracking-[-0.04em] text-navy-900">{formatMetric(avgOutputFps, 1)}</strong>
          </div>
          <div className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/70 p-5">
            <span className="block text-sm text-secondaryGray-500">平均丢帧率</span>
            <strong className="mt-2 block text-3xl font-extrabold tracking-[-0.04em] text-navy-900">{formatMetric(avgDropRate, 3)}</strong>
          </div>
        </div>
      </Panel>

      <Panel title="最近 DUT 登记" subtitle="待测芯片型号属于运维接入信息，不在首页和项目页固化为固定型号。">
        {tasks.length === 0 ? (
          <EmptyState title="暂无 DUT 登记" description="执行中心创建任务并绑定设备后，这里会显示最近录入的 DUT 型号。" />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {tasks.map((task) => (
              <div key={task.benchmark_task_id} className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/70 p-5">
                <div className="flex items-center justify-between gap-3">
                  <strong className="text-sm font-bold text-navy-900">{task.dut_model ?? '未登记 DUT'}</strong>
                  <StatusPill status={task.status} />
                </div>
                <p className="mt-2 text-sm text-secondaryGray-600">{task.project_name}</p>
                <p className="mt-1 text-xs text-secondaryGray-500">
                  绑定设备: {task.hil_config?.gateway_id ?? '未绑定'} / 模板: {task.benchmark_name}
                </p>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
