interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <strong className="empty-state__title">{title}</strong>
      <p className="empty-state__description">{description}</p>
    </div>
  );
}
