import { useEffect, useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { createCapture, listCaptures, startCapture, stopCapture } from '../../api/captures';
import { listGateways } from '../../api/gateways';
import type { CreateCapturePayload } from '../../api/types';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { ProgressBar } from '../../components/common/ProgressBar';
import { StatusPill } from '../../components/common/StatusPill';
import { formatDateTime, sortByActivity, terminalStatus, truncateMiddle } from '../../lib/format';

function defaultCaptureDir() {
  const stamp = new Date()
    .toISOString()
    .replace(/:/g, '')
    .replace(/\./g, '')
    .replace('T', '_')
    .slice(0, 15);
  return `/home/kavin/duckpark/captures/cap_${stamp}`;
}

export function CapturesPage() {
  const queryClient = useQueryClient();
  const gatewaysQuery = useQuery({
    queryKey: ['gateways'],
    queryFn: listGateways,
    refetchInterval: 5000
  });
  const capturesQuery = useQuery({
    queryKey: ['captures'],
    queryFn: () => listCaptures(),
    refetchInterval: 5000
  });

  const [gatewayId, setGatewayId] = useState('');
  const [source, setSource] = useState('hdmi_x1301');
  const [saveFormat, setSaveFormat] = useState('jpg');
  const [sampleFps, setSampleFps] = useState('2');
  const [maxFrames, setMaxFrames] = useState('300');
  const [saveDir, setSaveDir] = useState(defaultCaptureDir());
  const [note, setNote] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [autoStart, setAutoStart] = useState(true);

  useEffect(() => {
    if (!gatewayId && gatewaysQuery.data?.[0]) {
      setGatewayId(gatewaysQuery.data[0].gateway_id);
    }
  }, [gatewayId, gatewaysQuery.data]);

  const createMutation = useMutation({
    mutationFn: async () => {
      const payload: CreateCapturePayload = {
        gateway_id: gatewayId,
        source,
        save_format: saveFormat,
        sample_fps: Number(sampleFps),
        max_frames: Number(maxFrames),
        save_dir: saveDir,
        note: note || undefined
      };
      const created = await createCapture(payload);
      if (autoStart) {
        await startCapture(created.capture_id);
      }
      return created.capture_id;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['captures'] });
      void queryClient.invalidateQueries({ queryKey: ['gateways'] });
      setSaveDir(defaultCaptureDir());
      setNote('');
    }
  });

  const startMutation = useMutation({
    mutationFn: (captureId: string) => startCapture(captureId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['captures'] })
  });
  const stopMutation = useMutation({
    mutationFn: (captureId: string) => stopCapture(captureId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['captures'] })
  });

  const captures = sortByActivity(capturesQuery.data ?? []);
  const runningCount = captures.filter((capture) => capture.status === 'RUNNING').length;
  const completedCount = captures.filter((capture) => capture.status === 'COMPLETED').length;
  const failedCount = captures.filter((capture) => capture.status === 'FAILED').length;
  const totalSavedFrames = captures.reduce((sum, capture) => sum + capture.saved_frames, 0);
  const filteredCaptures = captures.filter((capture) => {
    const statusMatched = !statusFilter || capture.status === statusFilter;
    const keyword = searchKeyword.trim().toLowerCase();
    const searchMatched =
      !keyword ||
      capture.capture_id.toLowerCase().includes(keyword) ||
      capture.gateway_id.toLowerCase().includes(keyword) ||
      capture.save_dir.toLowerCase().includes(keyword);
    return statusMatched && searchMatched;
  });

  return (
    <div className="page-stack">
      <PageHeader
        title="Captures"
        description="创建、启动和查看采集任务。"
        actions={
          <button className="horizon-button-secondary" onClick={() => void queryClient.invalidateQueries({ queryKey: ['captures'] })} type="button">
            刷新
          </button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="teal" label="Running" value={runningCount} hint="正在由 Pi 网关采集中" />
        <MetricCard accent="blue" label="Completed" value={completedCount} hint="已经完成并有 manifest" />
        <MetricCard accent="rose" label="Failed" value={failedCount} hint="优先排查视频源或磁盘" />
        <MetricCard accent="orange" label="Saved Frames" value={totalSavedFrames} hint="所有 capture 已保存帧总和" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_320px]">
        <Panel title="创建采集任务">
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              createMutation.mutate();
            }}
          >
            <label className="field">
              <span>网关</span>
              <select value={gatewayId} onChange={(event) => setGatewayId(event.target.value)}>
                {(gatewaysQuery.data ?? []).map((gateway) => (
                  <option key={gateway.gateway_id} value={gateway.gateway_id}>
                    {gateway.name} ({gateway.gateway_id})
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>视频源</span>
              <select value={source} onChange={(event) => setSource(event.target.value)}>
                <option value="hdmi_x1301">hdmi_x1301</option>
                <option value="frame_stream">frame_stream</option>
              </select>
            </label>

            <label className="field">
              <span>保存格式</span>
              <select value={saveFormat} onChange={(event) => setSaveFormat(event.target.value)}>
                <option value="jpg">jpg</option>
                <option value="png">png</option>
                <option value="raw">raw</option>
              </select>
            </label>

            <label className="field">
              <span>采样帧率</span>
              <input value={sampleFps} onChange={(event) => setSampleFps(event.target.value)} />
            </label>

            <label className="field">
              <span>最大帧数</span>
              <input value={maxFrames} onChange={(event) => setMaxFrames(event.target.value)} />
            </label>

            <label className="field field--full">
              <span>保存目录</span>
              <input value={saveDir} onChange={(event) => setSaveDir(event.target.value)} />
            </label>

            <label className="field field--full">
              <span>备注</span>
              <textarea rows={3} value={note} onChange={(event) => setNote(event.target.value)} />
            </label>

            <label className="field field--checkbox">
              <input checked={autoStart} onChange={(event) => setAutoStart(event.target.checked)} type="checkbox" />
              <span>创建后立即启动</span>
            </label>

            {createMutation.error && <p className="inline-error">{createMutation.error.message}</p>}
            <div className="button-row">
              <button className="horizon-button" disabled={createMutation.isPending || !gatewayId} type="submit">
                {createMutation.isPending ? '提交中...' : autoStart ? '创建并启动' : '创建采集'}
              </button>
            </div>
          </form>
        </Panel>

        <Panel title="筛选器">
          <div className="form-grid">
            <label className="field">
              <span>状态</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">全部</option>
                {['CREATED', 'RUNNING', 'STOPPED', 'COMPLETED', 'FAILED', 'CANCELED'].map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>关键字</span>
              <input
                placeholder="capture_id / gateway / save_dir"
                value={searchKeyword}
                onChange={(event) => setSearchKeyword(event.target.value)}
              />
            </label>
          </div>
          <div className="mt-5 rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
            <span className="block text-[11px] font-extrabold uppercase tracking-[0.18em] text-secondaryGray-500">Write Path</span>
            <p className="mt-3 text-sm leading-6 text-secondaryGray-600">
              重点关注 `saved_frames`、`save_dir` 和 manifest 状态。
            </p>
          </div>
        </Panel>
      </div>

      <Panel title="采集列表" subtitle="查看采集状态、保存帧数和目录。">
        {filteredCaptures.length === 0 ? (
          <EmptyState title="没有匹配的采集任务" description="当前筛选条件下没有 capture 记录。" />
        ) : (
          <div className="flex flex-col gap-4">
            {filteredCaptures.map((capture) => (
              <div key={capture.capture_id} className="rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/60 p-5 shadow-card">
                <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <StatusPill status={capture.status} />
                      <Link className="text-sm font-bold text-brand-600" to={`/captures/${capture.capture_id}`}>
                        {truncateMiddle(capture.capture_id, 8)}
                      </Link>
                    </div>
                    <strong className="mt-3 block text-xl font-extrabold tracking-[-0.03em] text-navy-900">{capture.gateway_id}</strong>
                    <p className="mt-1 text-sm text-secondaryGray-600">{capture.source}</p>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {!terminalStatus(capture.status) && capture.status !== 'RUNNING' && (
                      <button
                        className="horizon-button-secondary"
                        disabled={startMutation.isPending}
                        onClick={() => startMutation.mutate(capture.capture_id)}
                        type="button"
                      >
                        启动
                      </button>
                    )}
                    {!terminalStatus(capture.status) && capture.status === 'RUNNING' && (
                      <button
                        className="inline-flex min-h-11 items-center justify-center rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm font-bold text-rose-600 transition hover:-translate-y-0.5"
                        disabled={stopMutation.isPending}
                        onClick={() => stopMutation.mutate(capture.capture_id)}
                        type="button"
                      >
                        停止
                      </button>
                    )}
                    <Link className="horizon-button" to={`/captures/${capture.capture_id}`}>
                      详情
                    </Link>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                  <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                    <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Format</span>
                    <strong className="mt-2 block text-sm text-navy-900">
                      {capture.save_format} / {capture.sample_fps} FPS
                    </strong>
                  </div>
                  <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                    <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Frame Limit</span>
                    <strong className="mt-2 block text-sm text-navy-900">{capture.max_frames ?? '-'} 帧</strong>
                  </div>
                  <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                    <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Saved Frames</span>
                    <strong className="mt-2 block text-sm text-navy-900">{capture.saved_frames}</strong>
                  </div>
                  <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                    <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Updated</span>
                    <strong className="mt-2 block text-sm text-navy-900">{formatDateTime(capture.updated_at_utc)}</strong>
                  </div>
                  <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                    <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">Started</span>
                    <strong className="mt-2 block text-sm text-navy-900">{formatDateTime(capture.started_at_utc)}</strong>
                  </div>
                </div>

                <div className="mt-4 rounded-[18px] border border-white/80 bg-white px-4 py-4">
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-sm font-semibold text-secondaryGray-600">{truncateMiddle(capture.save_dir, 22)}</span>
                    <span className="text-sm font-bold text-navy-900">
                      {capture.saved_frames}/{capture.max_frames ?? 0}
                    </span>
                  </div>
                  <div className="mt-3">
                    <ProgressBar
                      label="保存进度"
                      max={capture.max_frames ?? Math.max(capture.saved_frames, 1)}
                      value={capture.saved_frames}
                    />
                  </div>
                </div>
                {capture.error_reason && <p className="mt-4 text-sm text-rose-600">{capture.error_reason}</p>}
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
