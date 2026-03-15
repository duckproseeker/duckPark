interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="rounded-[12px] border border-slate-700 bg-slate-900/60 p-4">
      <strong className="block text-sm font-bold text-slate-100">{title}</strong>
      <p className="mt-2 text-xs leading-5 text-slate-400">{description}</p>
    </div>
  );
}
