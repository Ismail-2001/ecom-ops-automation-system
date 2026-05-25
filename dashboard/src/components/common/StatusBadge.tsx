import React from 'react';
import { getStatusColors } from '../../utils/riskColors';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const colors = getStatusColors(status);
  
  // Format text label
  let label = status.toUpperCase();
  if (status === 'executing') label = 'EXECUTING...';
  if (status === 'shadow') label = 'SHADOW MODE';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider border ${colors.bg} ${colors.text} ${colors.border} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${colors.dot} mr-1.5`} />
      {label}
    </span>
  );
};

export default StatusBadge;
