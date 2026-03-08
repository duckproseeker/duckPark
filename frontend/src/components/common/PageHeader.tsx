import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description: string;
  actions?: ReactNode;
  eyebrow?: string;
  chips?: string[];
}

const defaultChips = ['芯片测评平台', 'CARLA 场景仿真', '工程报告'];

export function PageHeader({
  title,
  description,
  actions,
  eyebrow = 'Chip Evaluation Workspace',
  chips = defaultChips
}: PageHeaderProps) {
  return (
    <div className="horizon-card bg-hero-grid mb-5 overflow-hidden rounded-[30px] border border-white/90 bg-white/95 px-6 py-6 md:px-7 md:py-7">
      <div className="flex flex-col gap-6">
        <div className="min-w-0">
          <div className="mb-3 flex flex-wrap gap-2">
            {chips.map((chip) => (
              <span key={chip} className="horizon-chip">
                {chip}
              </span>
            ))}
          </div>
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-secondaryGray-500">
            {eyebrow}
          </p>
          <h1 className="mt-3 text-4xl font-extrabold tracking-[-0.04em] text-navy-900 md:text-5xl">{title}</h1>
          <p className="mt-3 max-w-4xl text-sm leading-7 text-secondaryGray-600 md:text-base">{description}</p>
        </div>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-3">
            <span className="rounded-2xl border border-secondaryGray-200 bg-white/90 px-4 py-2 text-xs font-bold text-secondaryGray-600 shadow-card">
              场景执行编排
            </span>
            <span className="rounded-2xl border border-secondaryGray-200 bg-white/90 px-4 py-2 text-xs font-bold text-secondaryGray-600 shadow-card">
              设备与采集遥测
            </span>
            <span className="rounded-2xl border border-secondaryGray-200 bg-white/90 px-4 py-2 text-xs font-bold text-secondaryGray-600 shadow-card">
              报告与指标沉淀
            </span>
          </div>
          {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
        </div>
      </div>
    </div>
  );
}
