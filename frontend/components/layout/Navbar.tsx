"use client";

import React, { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { LogOut, User as UserIcon, Shield, Menu, X, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function Navbar() {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/dashboard", roles: ["admin", "viewer"] },
    { name: "Mobile Collector", href: "/collectors/mobile", roles: ["admin", "collector"] },
    { name: "Events", href: "/events", roles: ["admin", "collector", "viewer"] },
    { name: "Guests", href: "/guests", roles: ["admin", "collector", "viewer"] },
    { name: "Transactions", href: "/transactions", roles: ["admin", "collector", "viewer"] },
    { name: "Collectors", href: "/collectors", roles: ["admin"] },
    { name: "Physical Gifts", href: "/gifts", roles: ["admin", "collector", "viewer"] },
    { name: "Reconciliation", href: "/reconciliation", roles: ["admin", "collector"] },
    { name: "Reports", href: "/reports", roles: ["admin", "viewer"] },
    { name: "Audit Logs", href: "/audit-logs", roles: ["admin"] },
  ];

  const visibleItems = navItems.filter((item) =>
    user ? item.roles.includes(user.role) : true
  );

  return (
    <header className="h-16 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl sticky top-0 z-20 flex items-center justify-between px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <div className="lg:hidden flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <span className="font-bold text-sm bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
            GiftLedger
          </span>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-100/60 dark:bg-slate-800/60 px-3 py-1.5 rounded-full border border-slate-200/50 dark:border-slate-700/50">
          <Shield className="w-3.5 h-3.5 text-indigo-500" />
          <span>Secured Ledger Environment</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {user && (
          <div className="flex items-center gap-2">
            <Badge variant={user.role === "admin" ? "purple" : user.role === "collector" ? "info" : "neutral"}>
              {user.role.toUpperCase()}
            </Badge>
            <span className="hidden md:inline text-xs font-medium text-slate-700 dark:text-slate-300">
              {user.username}
            </span>
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={() => logout()}
          className="rounded-xl border-slate-200 dark:border-slate-800 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/50"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Sign Out</span>
        </Button>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-x-0 top-16 bg-white/95 dark:bg-slate-900/95 backdrop-blur-2xl border-b border-slate-200 dark:border-slate-800 p-4 shadow-xl z-40 space-y-1">
          {visibleItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileMenuOpen(false)}
              className={cn(
                "block px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors",
                pathname === item.href
                  ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
              )}
            >
              {item.name}
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}
