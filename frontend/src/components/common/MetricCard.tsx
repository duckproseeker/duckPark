import type { ReactNode } from 'react';

import clsx from 'clsx';

interface MetricCardProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  accent?: 'blue' | 'violet' | 'teal' | 'orange' | 'rose';
}

const accentClasses: Record<NonNullable<MetricCardProps['accent']>, string> = {
  blue: 'from-brand-500 to-accent-500',
  violet: 'from-violet-500 to-indigo-500',
  teal: 'from-emerald-500 to-cyan-400',
  orange: 'from-amber-400 to-orange-500',
  rose: 'from-rose-400 to-rose-500'
};

export function MetricCard({ label, value, hint, accent = 'blue' }: MetricCardProps) {
  return (
    <div className="horizon-card relative overflow-hidden rounded-[14px] px-4 py-4">
      <div className={clsx('absolute inset-x-0 top-0 h-1 bg-gradient-to-r', accentClasses[accent])} />
      <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p>
      <strong className="mt-2 block text-[28px] font-extrabold leading-none tracking-[-0.04em] text-slate-100">
        {value}
      </strong>
      {hint && <span className="mt-2 block text-xs text-slate-400">{hint}</span>}
    </div>
  );
}
