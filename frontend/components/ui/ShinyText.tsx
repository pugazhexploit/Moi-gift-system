"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface ShinyTextProps {
  children: React.ReactNode;
  className?: string;
  shimmerWidth?: number;
}

export function ShinyText({
  children,
  className,
}: ShinyTextProps) {
  return (
    <span
      className={cn(
        "inline-block bg-gradient-to-r from-slate-900 via-indigo-600 to-slate-900 dark:from-slate-100 dark:via-indigo-300 dark:to-slate-100 bg-[200%_auto] bg-clip-text text-transparent animate-shimmer font-semibold",
        className
      )}
      style={{
        animation: "shine 4s linear infinite",
      }}
    >
      {children}
    </span>
  );
}
