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
    <section className={clsx('horizon-card rounded-[24px] border border-white/90 bg-white/95', className)}>
      {(title || subtitle || actions) && (
        <header className="flex items-start justify-between gap-4 px-5 pb-0 pt-5 md:px-6 md:pt-6">
          <div>
            {title && <h2 className="text-lg font-extrabold tracking-[-0.02em] text-navy-900">{title}</h2>}
            {subtitle && <p className="mt-1 text-sm leading-6 text-secondaryGray-600">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-3">{actions}</div>}
        </header>
      )}
      <div className="px-5 py-5 md:px-6 md:py-6">{children}</div>
    </section>
  );
}
