import { cn } from "@/lib/utils";
import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info" | "purple" | "neutral";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  const styles = {
    default: "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800",
    warning: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800",
    danger: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800",
    info: "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/50 dark:text-sky-300 dark:border-sky-800",
    purple: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/50 dark:text-purple-300 dark:border-purple-800",
    neutral: "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors",
        styles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  switch (s) {
    case "verified":
    case "active":
    case "completed":
    case "valid":
      return <Badge variant="success">{status}</Badge>;
    case "locked":
      return <Badge variant="purple">{status}</Badge>;
    case "pending":
    case "submitted":
    case "draft":
      return <Badge variant="warning">{status}</Badge>;
    case "rejected":
    case "mismatch":
    case "cancelled":
    case "suspended":
      return <Badge variant="danger">{status}</Badge>;
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
}
