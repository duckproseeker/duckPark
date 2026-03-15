import type { PropsWithChildren, ReactNode } from 'react';
import clsx from 'clsx';

interface DetailPanelProps extends PropsWithChildren {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}

export function DetailPanel({ title, subtitle, actions, className, children }: DetailPanelProps) {
  return (
    <section className={clsx('detail-panel', className)}>
      <header className="detail-panel__header">
        <div>
          <h2 className="detail-panel__title">{title}</h2>
          {subtitle && <p className="detail-panel__subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="detail-panel__actions">{actions}</div>}
      </header>
      <div className="detail-panel__body">{children}</div>
    </section>
  );
}
