"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyButton } from "@/components/ui/ShinyButton";
import { ShinyText } from "@/components/ui/ShinyText";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Event } from "@/types/api";
import { FileBarChart, Download, FileSpreadsheet, FileText, Printer, CheckCircle2 } from "lucide-react";

export default function ReportsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [eventReportData, setEventReportData] = useState<any | null>(null);
  const [exporting, setExporting] = useState<string | null>(null);

  useEffect(() => {
    api.get<{ items: Event[] }>("/api/events?limit=50").then((res) => {
      if (res.data?.items?.length) {
        setEvents(res.data.items);
        setSelectedEventId(res.data.items[0].event_id);
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedEventId) return;
    api.get<any>(`/api/reports/event/${selectedEventId}`).then((res) => {
      if (res.data) setEventReportData(res.data);
    });
  }, [selectedEventId]);

  const handleExport = async (type: "event" | "guests" | "reconciliation", format: "csv" | "xlsx" | "pdf") => {
    const key = `${type}-${format}`;
    setExporting(key);
    try {
      let endpoint = "";
      if (type === "event") endpoint = `/api/reports/event/${selectedEventId}/export?format=${format}`;
      if (type === "guests") endpoint = `/api/reports/guests/export?format=${format}&event_id=${selectedEventId}`;
      if (type === "reconciliation") endpoint = `/api/reports/reconciliation/export?format=${format}&event_id=${selectedEventId}`;

      // Fetch blob with cookie
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "X-CSRF-Token": document.cookie.match(new RegExp("(^|;\\s*)gl_csrf=([^;]+)"))?.[2] || "",
        },
        credentials: "include",
      });

      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${type}_report_${selectedEventId || "all"}.${format === "xlsx" ? "xlsx" : format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast(`Exported ${format.toUpperCase()} successfully!`);
    } catch (err: any) {
      toast(err?.message || "Export error", "error");
    } finally {
      setExporting(null);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <ShinyText>Executive Reporting & Audited Exports</ShinyText>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Compliant financial balance sheets, guest ledgers, and multi-format document downloads.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              className="text-xs font-medium rounded-xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-slate-800 dark:text-slate-200"
            >
              {events.map((evt) => (
                <option key={evt.event_id} value={evt.event_id}>
                  {evt.event_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Event Summary Report Card */}
        {eventReportData && (
          <SpotlightCard className="p-6">
            <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">
                  Event Comprehensive Balance Sheet
                </h3>
                <p className="text-xs text-slate-400">
                  {eventReportData.event_name} ({eventReportData.event_id})
                </p>
              </div>

              {/* Export Buttons */}
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  loading={exporting === "event-csv"}
                  onClick={() => handleExport("event", "csv")}
                  className="text-xs rounded-xl"
                >
                  <Download className="w-3.5 h-3.5 mr-1 text-emerald-400" />
                  CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  loading={exporting === "event-xlsx"}
                  onClick={() => handleExport("event", "xlsx")}
                  className="text-xs rounded-xl"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 mr-1 text-sky-400" />
                  Excel
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  loading={exporting === "event-pdf"}
                  onClick={() => handleExport("event", "pdf")}
                  className="text-xs rounded-xl"
                >
                  <FileText className="w-3.5 h-3.5 mr-1 text-rose-400" />
                  PDF
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <p className="text-slate-400">Total Contribution</p>
                <p className="text-lg font-bold text-white mt-1">
                  {formatCurrency(eventReportData.total_contributions)}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <p className="text-slate-400">Cash In Hand</p>
                <p className="text-lg font-bold text-emerald-400 mt-1">
                  {formatCurrency(eventReportData.total_cash)}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <p className="text-slate-400">Online / Digital</p>
                <p className="text-lg font-bold text-sky-400 mt-1">
                  {formatCurrency(eventReportData.total_online)}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <p className="text-slate-400">Total Guests</p>
                <p className="text-lg font-bold text-indigo-400 mt-1">
                  {eventReportData.total_guests} Attendees
                </p>
              </div>
            </div>
          </SpotlightCard>
        )}

        {/* Dedicated Report Export Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SpotlightCard className="p-6">
            <h3 className="text-sm font-bold text-white mb-1">
              Guest Ledger & Contributions Export
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Export every guest with their total monetary contributions and physical presents.
            </p>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                loading={exporting === "guests-csv"}
                onClick={() => handleExport("guests", "csv")}
                className="text-xs rounded-xl"
              >
                Download CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                loading={exporting === "guests-xlsx"}
                onClick={() => handleExport("guests", "xlsx")}
                className="text-xs rounded-xl"
              >
                Download Excel (.xlsx)
              </Button>
            </div>
          </SpotlightCard>

          <SpotlightCard className="p-6">
            <h3 className="text-sm font-bold text-white mb-1">
              Reconciliation Discrepancy Export
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Audit export of shift drawer expected sums vs actual counted currencies.
            </p>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                loading={exporting === "reconciliation-csv"}
                onClick={() => handleExport("reconciliation", "csv")}
                className="text-xs rounded-xl"
              >
                Download CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                loading={exporting === "reconciliation-xlsx"}
                onClick={() => handleExport("reconciliation", "xlsx")}
                className="text-xs rounded-xl"
              >
                Download Excel (.xlsx)
              </Button>
            </div>
          </SpotlightCard>
        </div>
      </div>
    </AppShell>
  );
}
