interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 p-5">
      <strong className="block text-base font-bold text-navy-900">{title}</strong>
      <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{description}</p>
    </div>
  );
}
