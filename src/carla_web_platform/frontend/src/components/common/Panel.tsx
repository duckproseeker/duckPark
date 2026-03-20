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
    <section className={clsx('panel horizon-card', className)}>
      {(title || subtitle || actions) && (
        <header className="panel__header">
          <div className="panel__copy">
            {title && <h2 className="panel__title">{title}</h2>}
            {subtitle && <p className="panel__subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="panel__actions">{actions}</div>}
        </header>
      )}
      <div className="panel__body">{children}</div>
    </section>
  );
}
