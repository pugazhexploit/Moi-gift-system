"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Users,
  CreditCard,
  UserCheck,
  Gift,
  Scale,
  FileBarChart,
  ShieldCheck,
  Smartphone,
  Settings,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard, roles: ["admin", "viewer"] },
    { name: "Mobile Collector", href: "/collectors/mobile", icon: Smartphone, roles: ["admin", "collector"] },
    { name: "Events", href: "/events", icon: Calendar, roles: ["admin", "collector", "viewer"] },
    { name: "Guests", href: "/guests", icon: Users, roles: ["admin", "collector", "viewer"] },
    { name: "Transactions", href: "/transactions", icon: CreditCard, roles: ["admin", "collector", "viewer"] },
    { name: "Collectors", href: "/collectors", icon: UserCheck, roles: ["admin"] },
    { name: "Physical Gifts", href: "/gifts", icon: Gift, roles: ["admin", "collector", "viewer"] },
    { name: "Reconciliation", href: "/reconciliation", icon: Scale, roles: ["admin", "collector"] },
    { name: "Reports", href: "/reports", icon: FileBarChart, roles: ["admin", "viewer"] },
    { name: "Audit Logs", href: "/audit-logs", icon: ShieldCheck, roles: ["admin"] },
    { name: "Settings", href: "/settings", icon: Settings, roles: ["admin", "collector", "viewer"] },
  ];

  const visibleItems = navItems.filter((item) =>
    user ? item.roles.includes(user.role) : true
  );

  return (
    <aside className="w-64 border-r border-slate-200/80 dark:border-slate-800/80 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl flex flex-col h-screen fixed top-0 left-0 z-30 transition-all">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-2.5 px-6 border-b border-slate-200/60 dark:border-slate-800/60">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <span className="font-bold text-base tracking-tight bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
            GiftLedger
          </span>
          <span className="block text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 tracking-wider">
            Fintech Suite
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all group",
                isActive
                  ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 font-semibold shadow-sm border border-indigo-100 dark:border-indigo-900/50"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100/80 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100"
              )}
            >
              <Icon
                className={cn(
                  "w-4 h-4 transition-colors",
                  isActive
                    ? "text-indigo-600 dark:text-indigo-400"
                    : "text-slate-400 group-hover:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300"
                )}
              />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer / User status preview */}
      <div className="p-4 border-t border-slate-200/60 dark:border-slate-800/60">
        <div className="flex items-center gap-3 p-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-slate-700/50">
          <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 flex items-center justify-center text-xs font-bold uppercase">
            {user?.username?.[0] || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-800 dark:text-slate-200 truncate">
              {user?.username || "Guest"}
            </p>
            <p className="text-[10px] text-slate-400 capitalize truncate">
              {user?.role || "Session"}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
