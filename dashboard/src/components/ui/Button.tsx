import React from 'react';
import { cn } from '../../utils/cn';
import { motion, type HTMLMotionProps } from 'framer-motion';

export interface ButtonProps extends HTMLMotionProps<"button"> {
  variant?: 'default' | 'outline' | 'ghost' | 'destructive' | 'secondary';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    
    const variants = {
      default: "bg-accent text-accent-foreground shadow-lg hover:bg-blue-500 hover:shadow-blue-500/20",
      destructive: "bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white",
      outline: "border border-white/10 bg-transparent hover:bg-white/5 text-slate-300",
      secondary: "bg-muted text-foreground hover:bg-slate-800",
      ghost: "hover:bg-white/5 text-slate-400 hover:text-white",
    };

    const sizes = {
      default: "h-9 px-4 py-2",
      sm: "h-8 rounded-md px-3 text-xs",
      lg: "h-10 rounded-md px-8",
      icon: "h-9 w-9",
    };

    return (
      <motion.button
        ref={ref}
        whileTap={{ scale: 0.98 }}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
