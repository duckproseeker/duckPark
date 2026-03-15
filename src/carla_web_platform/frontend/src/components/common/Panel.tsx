import type { PropsWithChildren, ReactNode } from 'react';

import clsx from 'clsx';

interface PanelProps extends PropsWithChildren {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}

export function Panel({ title, subtitle, actions, className, children }: PanelProps) {
  return (
    <section className={clsx('horizon-card rounded-[14px]', className)}>
      {(title || subtitle || actions) && (
        <header className="flex items-start justify-between gap-4 px-4 pb-0 pt-4 md:px-5 md:pt-5">
          <div>
            {title && <h2 className="text-base font-extrabold tracking-[-0.02em] text-slate-100">{title}</h2>}
            {subtitle && <p className="mt-1 text-xs leading-5 text-slate-400">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-3">{actions}</div>}
        </header>
      )}
      <div className="px-4 py-4 md:px-5 md:py-5">{children}</div>
    </section>
  );
}
