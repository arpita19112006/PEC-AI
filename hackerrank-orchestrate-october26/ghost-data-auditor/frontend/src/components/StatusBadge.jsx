const map = {
  COMPLETE: 'success',
  INCOMPLETE: 'warning',
  NOT_APPLICABLE: 'neutral',
  PENDING: 'neutral',
};

export default function StatusBadge({ status }) {
  const className = map[status] || 'neutral';
  return <span className={`status-badge ${className}`}>{status || 'PENDING'}</span>;
}
