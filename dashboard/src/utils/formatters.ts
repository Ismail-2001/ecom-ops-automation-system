import { format, formatDistanceToNow, parseISO } from 'date-fns';

export const formatCurrency = (value: number | null): string => {
  if (value === null) return '—';
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  return formatter.format(value);
};

export const formatPercentage = (value: number | null): string => {
  if (value === null) return '—';
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
};

export const formatDateTime = (dateString: string | null): string => {
  if (!dateString) return '—';
  try {
    const date = parseISO(dateString);
    return format(date, 'MMM d, yyyy h:mm a');
  } catch (e) {
    return dateString;
  }
};

export const formatTimeAgo = (dateString: string | null): string => {
  if (!dateString) return '—';
  try {
    const date = parseISO(dateString);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch (e) {
    return dateString;
  }
};
export const getCountdown = (dateString: string | null): string => {
  if (!dateString) return '';
  try {
    const expiry = parseISO(dateString).getTime();
    const now = new Date().getTime();
    const diff = expiry - now;
    if (diff <= 0) return 'Expired';
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours > 0 ? `${hours}h ` : ''}${minutes}m`;
  } catch (e) {
    return '';
  }
};
