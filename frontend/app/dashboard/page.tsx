"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyText } from "@/components/ui/ShinyText";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { DashboardData, Event } from "@/types/api";
import {
  Users,
  CreditCard,
  Banknote,
  Globe,
  Gift,
  CheckCircle2,
  Clock,
  UserCheck,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  Filter,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#f43f5e", "#8b5cf6"];

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const fetchData = async (eventId?: string) => {
    setLoading(true);
    try {
      const query = eventId ? `?event_id=${eventId}` : "";
      const res = await api.get<DashboardData>(`/api/dashboard${query}`);
      if (res.data) setData(res.data);

      const evtRes = await api.get<{ items: Event[] }>("/api/events?limit=100");
      if (evtRes.data?.items) setEvents(evtRes.data.items);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(selectedEventId);
  }, [selectedEventId]);

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Top Filter Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <ShinyText>Executive Financial Dashboard</ShinyText>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Real-time cash reconciliation, verified contributions & collector status
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <select
                value={selectedEventId}
                onChange={(e) => setSelectedEventId(e.target.value)}
                className="text-xs font-medium rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Events (Global View)</option>
                {events.map((evt) => (
                  <option key={evt.event_id} value={evt.event_id}>
                    {evt.event_name} ({evt.event_id})
                  </option>
                ))}
              </select>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchData(selectedEventId)}
              className="rounded-xl"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
          </div>
        </div>

        {/* 9 KPI Metrics using React Bits SpotlightCard */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {/* Total Contributions */}
          <SpotlightCard spotlightColor="rgba(99, 102, 241, 0.2)" className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Total Collections
              </span>
              <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                <CreditCard className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {formatCurrency(data?.total_contributions)}
              </span>
            </div>
            <div className="mt-2 flex items-center text-[11px] text-emerald-600 dark:text-emerald-400 gap-1 font-medium">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Authoritative Ledger Sum</span>
            </div>
          </SpotlightCard>

          {/* Cash Total */}
          <SpotlightCard spotlightColor="rgba(16, 185, 129, 0.2)" className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Physical Cash
              </span>
              <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
                <Banknote className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {formatCurrency(data?.total_cash)}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400">
              Shift drawers & cash envelopes
            </div>
          </SpotlightCard>

          {/* Online / UPI Total */}
          <SpotlightCard spotlightColor="rgba(14, 165, 233, 0.2)" className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                UPI / Digital
              </span>
              <div className="p-2 rounded-xl bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400">
                <Globe className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {formatCurrency(data?.total_online)}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400">
              Instant digital transfers
            </div>
          </SpotlightCard>

          {/* Verified Amount */}
          <SpotlightCard spotlightColor="rgba(139, 92, 246, 0.2)" className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Verified Funds
              </span>
              <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
                {formatCurrency(data?.verified_amount)}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400">
              Admin confirmed transactions
            </div>
          </SpotlightCard>

          {/* Pending Verification */}
          <SpotlightCard spotlightColor="rgba(245, 158, 11, 0.2)" className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Pending Verification
              </span>
              <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold tracking-tight text-amber-600 dark:text-amber-400">
                {formatCurrency(data?.pending_amount)}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400">
              Awaiting admin approval
            </div>
          </SpotlightCard>

          {/* Total Registered Guests */}
          <SpotlightCard spotlightColor="rgba(99, 102, 241, 0.2)" className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Registered Guests
              </span>
              <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {data?.total_guests || 0}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400">
              Total guests with QR codes
            </div>
          </SpotlightCard>

          {/* Physical Gifts */}
          <SpotlightCard spotlightColor="rgba(244, 63, 94, 0.2)" className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Physical Gift Items
              </span>
              <div className="p-2 rounded-xl bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400">
                <Gift className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {data?.total_gift_items || 0}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400">
              Catalogued non-monetary items
            </div>
          </SpotlightCard>

          {/* Unreconciled Cash */}
          <SpotlightCard spotlightColor="rgba(245, 158, 11, 0.2)" className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Unreconciled Cash
              </span>
              <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {formatCurrency(data?.unreconciled_amount)}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400">
              Held in active collector shifts
            </div>
          </SpotlightCard>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline Trend Chart */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 p-6 backdrop-blur-xl shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">
              Hourly Contribution Volume
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
              Financial influx trend across the event duration
            </p>

            <div className="h-64 w-full">
              {data?.hourly_collection && data.hourly_collection.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.hourly_collection}>
                    <defs>
                      <linearGradient id="colorAmt" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="hour" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "0.75rem",
                        fontSize: "0.75rem",
                      }}
                      formatter={(val: any) => [formatCurrency(val), "Amount"]}
                    />
                    <Area
                      type="monotone"
                      dataKey="amount"
                      stroke="#6366f1"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorAmt)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">
                  No chronological distribution recorded yet
                </div>
              )}
            </div>
          </div>

          {/* Payment Method Breakdown */}
          <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 p-6 backdrop-blur-xl shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">
              Payment Methods
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
              Cash vs UPI / Bank distribution
            </p>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-slate-700/50">
                <div className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="text-xs font-medium">Cash</span>
                </div>
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {formatCurrency(data?.total_cash)}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-slate-700/50">
                <div className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full bg-sky-500" />
                  <span className="text-xs font-medium">Online (UPI / Transfer)</span>
                </div>
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {formatCurrency(data?.total_online)}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-slate-700/50">
                <div className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full bg-indigo-500" />
                  <span className="text-xs font-medium">Active Collectors</span>
                </div>
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {data?.number_of_collectors || 0} Staff
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
