import React from 'react';
import { cn } from '../../utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'destructive' | 'outline' | 'warning';
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "border-transparent bg-accent text-accent-foreground shadow hover:bg-blue-500",
    success: "border-transparent bg-emerald-500/15 text-emerald-400 border border-emerald-500/20",
    destructive: "border-transparent bg-red-500/15 text-red-400 border border-red-500/20",
    warning: "border-transparent bg-amber-500/15 text-amber-400 border border-amber-500/20",
    outline: "text-slate-400 border border-slate-700",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
