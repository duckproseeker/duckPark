import clsx from 'clsx';

interface StatusPillProps {
  status: string;
}

function toneForStatus(status: string) {
  switch (status) {
    case 'RUNNING':
    case 'READY':
    case 'COMPLETED':
      return 'success';
    case 'QUEUED':
    case 'STARTING':
    case 'STOPPING':
    case 'CREATED':
    case 'BUSY':
      return 'warning';
    case 'FAILED':
    case 'ERROR':
    case 'CANCELED':
    case 'STOPPED':
      return 'danger';
    default:
      return 'neutral';
  }
}

export function StatusPill({ status }: StatusPillProps) {
  const tone = toneForStatus(status);

  return (
    <span
      className={clsx(
        'inline-flex min-h-7 items-center justify-center rounded-full border px-3 py-1 text-[11px] font-extrabold uppercase tracking-[0.14em]',
        tone === 'success' && 'border-emerald-100 bg-emerald-50 text-emerald-600',
        tone === 'warning' && 'border-amber-100 bg-amber-50 text-amber-600',
        tone === 'danger' && 'border-rose-100 bg-rose-50 text-rose-600',
        tone === 'neutral' && 'border-secondaryGray-200 bg-secondaryGray-100 text-secondaryGray-600'
      )}
    >
      {status}
    </span>
  );
}
