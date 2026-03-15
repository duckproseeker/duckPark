export type StatusSemantic = 'RUNNING' | 'READY' | 'COMPLETED' | 'FAILED' | 'OFFLINE' | 'UNKNOWN';

const runningStatuses = new Set([
  'CREATED',
  'QUEUED',
  'STARTING',
  'RUNNING',
  'PAUSED',
  'STOPPING',
  'BUSY'
]);

const readyStatuses = new Set(['READY', 'ACTIVE', 'OFFICIAL', 'PILOT']);
const completedStatuses = new Set(['COMPLETED']);
const failedStatuses = new Set(['FAILED', 'ERROR', 'CANCELED', 'STOPPED', 'PARTIAL_FAILED']);
const offlineStatuses = new Set(['OFFLINE', 'ARCHIVED']);

function normalize(input: string | null | undefined) {
  return (input ?? '').trim().toUpperCase();
}

export function toStatusSemantic(status: string | null | undefined): StatusSemantic {
  const normalized = normalize(status);
  if (!normalized) {
    return 'UNKNOWN';
  }
  if (runningStatuses.has(normalized)) {
    return 'RUNNING';
  }
  if (readyStatuses.has(normalized)) {
    return 'READY';
  }
  if (completedStatuses.has(normalized)) {
    return 'COMPLETED';
  }
  if (failedStatuses.has(normalized)) {
    return 'FAILED';
  }
  if (offlineStatuses.has(normalized)) {
    return 'OFFLINE';
  }
  return 'UNKNOWN';
}

export function statusToneClass(semantic: StatusSemantic) {
  if (semantic === 'RUNNING') {
    return 'status-badge--running';
  }
  if (semantic === 'READY') {
    return 'status-badge--ready';
  }
  if (semantic === 'COMPLETED') {
    return 'status-badge--completed';
  }
  if (semantic === 'FAILED') {
    return 'status-badge--failed';
  }
  if (semantic === 'OFFLINE') {
    return 'status-badge--offline';
  }
  return 'status-badge--unknown';
}
