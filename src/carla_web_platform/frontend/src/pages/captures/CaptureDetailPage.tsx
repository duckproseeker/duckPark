import { useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';

import { getCapture, getCaptureFrames, getCaptureManifest, stopCapture } from '../../api/captures';
import { EmptyState } from '../../components/common/EmptyState';
import { JsonBlock } from '../../components/common/JsonBlock';
import { KeyValueGrid } from '../../components/common/KeyValueGrid';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { ProgressBar } from '../../components/common/ProgressBar';
import { StatusPill } from '../../components/common/StatusPill';
import { formatBytes, formatDateTime, terminalStatus } from '../../lib/format';

export function CaptureDetailPage() {
  const { captureId = '' } = useParams();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const captureQuery = useQuery({
    queryKey: ['captures', captureId],
    queryFn: () => getCapture(captureId),
    enabled: Boolean(captureId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'RUNNING' ? 3000 : false;
    }
  });

  const manifestQuery = useQuery({
    queryKey: ['captures', captureId, 'manifest'],
    queryFn: () => getCaptureManifest(captureId),
    enabled: Boolean(captureId),
    refetchInterval: 5000
  });

  const framesQuery = useQuery({
    queryKey: ['captures', captureId, 'frames', offset, limit],
    queryFn: () => getCaptureFrames(captureId, offset, limit),
    enabled: Boolean(captureId)
  });

  const stopMutation = useMutation({
    mutationFn: () => stopCapture(captureId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['captures', captureId] });
      void queryClient.invalidateQueries({ queryKey: ['captures'] });
      void queryClient.invalidateQueries({ queryKey: ['captures', captureId, 'manifest'] });
    }
  });

  const capture = captureQuery.data;
  const manifest = manifestQuery.data;
  const frames = framesQuery.data ?? [];
  const latestFrame = manifest?.frames[manifest.frames.length - 1] ?? null;

  if (!captureId) {
    return <EmptyState title="缺少 capture_id" description="路由参数里没有 capture_id。" />;
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Capture Detail"
        description={capture ? `${capture.capture_id} / ${capture.gateway_id}` : captureId}
        actions={
          <div className="button-row">
            <Link className="button button--secondary" to="/captures">
              返回列表
            </Link>
            {!terminalStatus(capture?.status ?? '') && capture?.status === 'RUNNING' && (
              <button className="button button--ghost-danger" disabled={stopMutation.isPending} onClick={() => stopMutation.mutate()} type="button">
                停止采集
              </button>
            )}
          </div>
        }
      />

      {!capture ? (
        <Panel>
          <p>加载中...</p>
        </Panel>
      ) : (
        <>
          <Panel title="采集摘要">
            <KeyValueGrid
              items={[
                { label: '状态', value: <StatusPill status={capture.status} /> },
                { label: '采集 ID', value: capture.capture_id },
                { label: '网关', value: capture.gateway_id },
                { label: '源', value: capture.source },
                { label: '保存格式', value: capture.save_format },
                { label: '采样帧率', value: capture.sample_fps },
                { label: '最大帧数', value: capture.max_frames ?? '-' },
                { label: '已保存帧数', value: capture.saved_frames },
                { label: '保存目录', value: capture.save_dir },
                { label: '创建时间', value: formatDateTime(capture.created_at_utc) },
                { label: '开始时间', value: formatDateTime(capture.started_at_utc) },
                { label: '结束时间', value: formatDateTime(capture.ended_at_utc) },
                { label: '错误原因', value: capture.error_reason ?? '-' }
              ]}
            />
          </Panel>

          <div className="two-column-grid">
            <Panel title="Manifest 摘要">
              {manifest ? (
                <>
                  <ProgressBar
                    label={`${manifest.saved_frames}/${manifest.max_frames ?? 0}`}
                    max={manifest.max_frames ?? Math.max(manifest.saved_frames, 1)}
                    value={manifest.saved_frames}
                  />
                  <KeyValueGrid
                    items={[
                      { label: '保存帧数', value: manifest.saved_frames },
                      { label: '帧列表长度', value: manifest.frames.length },
                      { label: '备注', value: manifest.note ?? '-' },
                      { label: 'manifest 状态', value: manifest.status }
                    ]}
                  />
                </>
              ) : (
                <p>加载中...</p>
              )}
            </Panel>

            <Panel title="采集验证">
              {manifest && latestFrame ? (
                <KeyValueGrid
                  items={[
                    { label: '最近一帧时间', value: formatDateTime(latestFrame.captured_at_utc) },
                    { label: '最近一帧路径', value: latestFrame.relative_path },
                    { label: '最近一帧尺寸', value: `${latestFrame.width ?? '-'} x ${latestFrame.height ?? '-'}` },
                    { label: '最近一帧大小', value: formatBytes(latestFrame.size_bytes) },
                    { label: 'Pi 保存目录', value: manifest.save_dir },
                    { label: '可以判定', value: 'CARLA 场景帧已经被 Pi 实际写盘' }
                  ]}
                />
              ) : (
                <EmptyState title="还没有采集证明" description="当 saved_frames 增长且 manifest 出现最近一帧记录时，才能确认 Pi 已经实际保存了数据。" />
              )}
            </Panel>
          </div>

          <Panel title="完整 Manifest">
            <JsonBlock value={manifest ?? { message: 'manifest 尚未加载完成。' }} />
          </Panel>

          <Panel
            title="帧清单"
            subtitle="这里只展示 manifest 同步到平台的记录，不直接浏览 Pi 本地图片内容。"
            actions={
              <div className="button-row">
                <button
                  className="button button--secondary"
                  disabled={offset === 0}
                  onClick={() => setOffset((value) => Math.max(0, value - limit))}
                  type="button"
                >
                  上一页
                </button>
                <button
                  className="button button--secondary"
                  disabled={frames.length < limit}
                  onClick={() => setOffset((value) => value + limit)}
                  type="button"
                >
                  下一页
                </button>
              </div>
            }
          >
            {frames.length === 0 ? (
              <EmptyState title="没有帧记录" description="采集尚未写入 manifest，或当前页没有数据。" />
            ) : (
              <div className="data-table">
                <div className="data-table__header">
                  <span>序号</span>
                  <span>时间</span>
                  <span>尺寸</span>
                  <span>大小</span>
                  <span>相对路径</span>
                </div>
                {frames.map((frame) => (
                  <div key={`${frame.frame_index}-${frame.relative_path}`} className="data-table__row">
                    <div className="data-table__cell">{frame.frame_index}</div>
                    <div className="data-table__cell">{formatDateTime(frame.captured_at_utc)}</div>
                    <div className="data-table__cell">
                      {frame.width ?? '-'} x {frame.height ?? '-'}
                    </div>
                    <div className="data-table__cell">{formatBytes(frame.size_bytes)}</div>
                    <div className="data-table__cell">{frame.relative_path}</div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </>
      )}
    </div>
  );
}
