import clsx from 'clsx';
import { statusToneClass, toStatusSemantic } from '../../lib/status';

interface StatusPillProps {
  status: string;
  canonical?: boolean;
}

export function StatusPill({ status, canonical = false }: StatusPillProps) {
  const semantic = toStatusSemantic(status);
  const label = canonical ? semantic : status;

  return (
    <span
      className={clsx(
        'status-badge inline-flex min-h-7 items-center justify-center rounded-full border px-3 py-1 text-[11px] font-extrabold uppercase tracking-[0.14em]',
        statusToneClass(semantic)
      )}
      title={status}
    >
      {label}
    </span>
  );
}
