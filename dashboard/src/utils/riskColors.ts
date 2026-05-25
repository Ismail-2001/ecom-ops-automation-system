import type { RiskLevel } from '../types/action';

export interface ColorScheme {
  bg: string;
  text: string;
  border: string;
  dot: string;
  icon: string;
}

export const getRiskColors = (level: RiskLevel): ColorScheme => {
  switch (level) {
    case 'critical':
      return {
        bg: 'bg-red-500/10',
        text: 'text-red-400',
        border: 'border-red-500/20',
        dot: 'bg-red-500',
        icon: 'stroke-red-400',
      };
    case 'high':
      return {
        bg: 'bg-orange-500/10',
        text: 'text-orange-400',
        border: 'border-orange-500/20',
        dot: 'bg-orange-500',
        icon: 'stroke-orange-400',
      };
    case 'medium':
      return {
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        border: 'border-amber-500/20',
        dot: 'bg-amber-500',
        icon: 'stroke-amber-400',
      };
    case 'low':
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/20',
        dot: 'bg-emerald-500',
        icon: 'stroke-emerald-400',
      };
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/20',
        dot: 'bg-slate-500',
        icon: 'stroke-slate-400',
      };
  }
};

export const getAgentColors = (agent: string): ColorScheme => {
  const norm = agent.toLowerCase();
  if (norm.includes('fraud')) {
    return {
      bg: 'bg-red-500/10',
      text: 'text-red-400',
      border: 'border-red-500/20',
      dot: 'bg-red-500',
      icon: 'stroke-red-400',
    };
  } else if (norm.includes('inventory')) {
    return {
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      border: 'border-amber-500/20',
      dot: 'bg-amber-500',
      icon: 'stroke-amber-400',
    };
  } else if (norm.includes('pricing')) {
    return {
      bg: 'bg-blue-500/10',
      text: 'text-blue-400',
      border: 'border-blue-500/20',
      dot: 'bg-blue-500',
      icon: 'stroke-blue-400',
    };
  } else if (norm.includes('reviews')) {
    return {
      bg: 'bg-violet-500/10',
      text: 'text-violet-400',
      border: 'border-violet-500/20',
      dot: 'bg-violet-500',
      icon: 'stroke-violet-400',
    };
  } else if (norm.includes('marketing')) {
    return {
      bg: 'bg-teal-500/10',
      text: 'text-teal-400',
      border: 'border-teal-500/20',
      dot: 'bg-teal-500',
      icon: 'stroke-teal-400',
    };
  } else {
    return {
      bg: 'bg-slate-500/10',
      text: 'text-slate-400',
      border: 'border-slate-500/20',
      dot: 'bg-slate-500',
      icon: 'stroke-slate-400',
    };
  }
};
export const getAgentLabel = (agent: string): string => {
  const norm = agent.toLowerCase();
  if (norm.includes('fraud')) return 'Fraud Agent';
  if (norm.includes('inventory')) return 'Inventory Agent';
  if (norm.includes('pricing')) return 'Pricing Agent';
  if (norm.includes('reviews')) return 'Reviews Agent';
  if (norm.includes('marketing')) return 'Marketing Agent';
  return agent;
};
export const getActionTypeLabel = (type: string): string => {
  switch (type) {
    case 'fraud_hold':
      return 'Hold Order';
    case 'purchase_order':
      return 'Create PO';
    case 'price_change':
      return 'Price Change';
    case 'review_response':
      return 'Post Review Response';
    case 'marketing_campaign':
      return 'Draft Campaign';
    default:
      return type;
  }
};
export const getStatusColors = (status: string): ColorScheme => {
  switch (status) {
    case 'pending':
      return {
        bg: 'bg-yellow-500/10',
        text: 'text-yellow-400',
        border: 'border-yellow-500/20',
        dot: 'bg-yellow-500',
        icon: 'stroke-yellow-400',
      };
    case 'approved':
    case 'executing':
      return {
        bg: 'bg-blue-500/10',
        text: 'text-blue-400',
        border: 'border-blue-500/20',
        dot: 'bg-blue-500',
        icon: 'stroke-blue-400',
      };
    case 'executed':
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/20',
        dot: 'bg-emerald-500',
        icon: 'stroke-emerald-400',
      };
    case 'rejected':
      return {
        bg: 'bg-red-500/10',
        text: 'text-red-400',
        border: 'border-red-500/20',
        dot: 'bg-red-500',
        icon: 'stroke-red-400',
      };
    case 'failed':
      return {
        bg: 'bg-rose-500/15',
        text: 'text-rose-400',
        border: 'border-rose-500/30',
        dot: 'bg-rose-500',
        icon: 'stroke-rose-400',
      };
    case 'expired':
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/20',
        dot: 'bg-slate-500',
        icon: 'stroke-slate-400',
      };
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/20',
        dot: 'bg-slate-500',
        icon: 'stroke-slate-400',
      };
  }
};
