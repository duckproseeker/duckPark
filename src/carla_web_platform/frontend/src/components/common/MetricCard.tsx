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
    <div className="horizon-card relative overflow-hidden rounded-[24px] px-5 py-5">
      <div className={clsx('absolute inset-x-0 top-0 h-1 bg-gradient-to-r', accentClasses[accent])} />
      <p className="text-sm font-semibold text-secondaryGray-500">{label}</p>
      <strong className="mt-3 block text-[32px] font-extrabold leading-none tracking-[-0.04em] text-navy-900">
        {value}
      </strong>
      {hint && <span className="mt-3 block text-sm text-secondaryGray-600">{hint}</span>}
    </div>
  );
}
