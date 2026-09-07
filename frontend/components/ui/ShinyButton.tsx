"use client";

import React, { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface ShinyButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  children: React.ReactNode;
}

export function ShinyButton({
  children,
  className,
  loading,
  disabled,
  ...props
}: ShinyButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        "relative inline-flex items-center justify-center px-6 py-2.5 rounded-xl font-medium text-white shadow-lg overflow-hidden transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none active:scale-95 group bg-gradient-to-r from-indigo-600 via-indigo-500 to-indigo-700 hover:shadow-indigo-500/25 hover:shadow-xl",
        className
      )}
      {...props}
    >
      <span className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out" />
      <span className="relative z-10 flex items-center gap-2">
        {loading && <Loader2 className="w-4 h-4 animate-spin text-current" />}
        {children}
      </span>
    </button>
  );
}
