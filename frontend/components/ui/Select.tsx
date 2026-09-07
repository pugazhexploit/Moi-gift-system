import React, { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, children, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={cn(
            "w-full px-3.5 py-2 rounded-xl text-sm border bg-white dark:bg-slate-900 text-slate-900 dark:text-white transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed",
            error
              ? "border-rose-300 dark:border-rose-700 focus:ring-rose-500"
              : "border-slate-300 dark:border-slate-700",
            className
          )}
          {...props}
        >
          {children}
        </select>
        {error && <p className="text-xs text-rose-600 dark:text-rose-400">{error}</p>}
      </div>
    );
  }
);
Select.displayName = "Select";
