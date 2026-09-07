"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyButton } from "@/components/ui/ShinyButton";
import { ShinyText } from "@/components/ui/ShinyText";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { Reconciliation, Event, Collector } from "@/types/api";
import { Scale, Plus, CheckCircle2, AlertTriangle, ShieldCheck, RefreshCw } from "lucide-react";

export default function ReconciliationPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [records, setRecords] = useState<Reconciliation[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [collectors, setCollectors] = useState<Collector[]>([]);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [loading, setLoading] = useState(true);

  // Modals
  const [submitModalOpen, setSubmitModalOpen] = useState(false);
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [activeRecord, setActiveRecord] = useState<Reconciliation | null>(null);
  const [resolveNotes, setResolveNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [collectorId, setCollectorId] = useState("");
  const [actualCash, setActualCash] = useState("");
  const [reason, setReason] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const evtRes = await api.get<{ items: Event[] }>("/api/events?limit=50");
      if (evtRes.data?.items) {
        setEvents(evtRes.data.items);
        if (!selectedEventId && evtRes.data.items.length) {
          setSelectedEventId(evtRes.data.items[0].event_id);
        }
      }

      const colRes = await api.get<{ items: Collector[] }>("/api/collectors?limit=50");
      if (colRes.data?.items) setCollectors(colRes.data.items);

      let url = "/api/reconciliation?limit=100";
      if (selectedEventId) url += `&event_id=${selectedEventId}`;
      const res = await api.get<{ items: Reconciliation[] }>(url);
      if (res.data?.items) setRecords(res.data.items);
    } catch (err: any) {
      toast(err?.message || "Failed to load reconciliation records", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedEventId]);

  const handleSubmitCash = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventId || !actualCash) {
      toast("Event and actual counted cash are required", "error");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/reconciliation", {
        event_id: selectedEventId,
        collector_id: collectorId || undefined,
        actual_cash: parseFloat(actualCash).toFixed(2),
        reason: reason || undefined,
      });
      toast("Shift cash drawer submitted for verification!");
      setSubmitModalOpen(false);
      setActualCash("");
      setReason("");
      loadData();
    } catch (err: any) {
      toast(err?.message || "Failed to submit cash reconciliation", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (id: string) => {
    try {
      await api.post(`/api/reconciliation/${id}/verify`);
      toast("Reconciliation verified by admin!");
      loadData();
    } catch (err: any) {
      toast(err?.message || "Failed to verify reconciliation", "error");
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRecord) return;
    setSubmitting(true);
    try {
      await api.post(`/api/reconciliation/${activeRecord.reconciliation_id}/resolve`, {
        action: "resolve",
        notes: resolveNotes || "Discrepancy reviewed and settled by admin",
      });
      toast("Discrepancy settled and resolved!");
      setResolveModalOpen(false);
      setResolveNotes("");
      loadData();
    } catch (err: any) {
      toast(err?.message || "Failed to resolve mismatch", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <ShinyText>Cash Reconciliation & Drawer Settlement</ShinyText>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Dual-party verification matching expected system totals against physical counted envelopes.
            </p>
          </div>

          <ShinyButton
            onClick={() => setSubmitModalOpen(true)}
            className="py-2.5 px-4 text-xs font-semibold rounded-xl"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Submit Shift Count
          </ShinyButton>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <select
            value={selectedEventId}
            onChange={(e) => setSelectedEventId(e.target.value)}
            className="text-xs font-medium rounded-xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-slate-800 dark:text-slate-200"
          >
            <option value="">All Events</option>
            {events.map((evt) => (
              <option key={evt.event_id} value={evt.event_id}>
                {evt.event_name}
              </option>
            ))}
          </select>
        </div>

        {/* Reconciliation Table */}
        <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200/80 dark:border-slate-800/80">
                <tr>
                  <th className="p-3.5">Reconciliation ID</th>
                  <th className="p-3.5">Collector</th>
                  <th className="p-3.5">Expected System Cash</th>
                  <th className="p-3.5">Actual Counted Cash</th>
                  <th className="p-3.5">Discrepancy (Diff)</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Submitted At</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
                {records.map((r) => {
                  const diffNum = parseFloat(r.difference) || 0;
                  return (
                    <tr key={r.reconciliation_id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="p-3.5 font-mono font-medium text-indigo-400">
                        {r.reconciliation_id}
                      </td>
                      <td className="p-3.5 font-mono">{r.collector_id}</td>
                      <td className="p-3.5 font-bold">{formatCurrency(r.expected_cash)}</td>
                      <td className="p-3.5 font-bold text-slate-900 dark:text-white">
                        {formatCurrency(r.actual_cash)}
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`font-bold ${
                            diffNum === 0
                              ? "text-emerald-400"
                              : diffNum < 0
                              ? "text-rose-400"
                              : "text-amber-400"
                          }`}
                        >
                          {diffNum > 0 ? `+${formatCurrency(diffNum)}` : formatCurrency(diffNum)}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <StatusBadge status={r.status} />
                      </td>
                      <td className="p-3.5 text-slate-400">{formatDateTime(r.submitted_at)}</td>
                      <td className="p-3.5 text-right space-x-1.5">
                        {user?.role === "admin" && (r.status === "submitted" || r.status === "pending") && (
                          <Button
                            variant="success"
                            size="sm"
                            onClick={() => handleVerify(r.reconciliation_id)}
                            className="py-1 px-2.5 text-xs"
                          >
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Verify Count
                          </Button>
                        )}

                        {user?.role === "admin" && r.status === "mismatch" && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => {
                              setActiveRecord(r);
                              setResolveModalOpen(true);
                            }}
                            className="py-1 px-2.5 text-xs"
                          >
                            <AlertTriangle className="w-3 h-3 mr-1" />
                            Resolve Mismatch
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {records.length === 0 && !loading && (
            <div className="p-8 text-center text-xs text-slate-400">
              No cash reconciliation submissions found.
            </div>
          )}
        </div>

        {/* Submit Count Modal */}
        <Modal
          isOpen={submitModalOpen}
          onClose={() => setSubmitModalOpen(false)}
          title="Submit Shift Cash Count"
          description="Count and declare the physical currency drawer amount"
          maxWidth="md"
        >
          <form onSubmit={handleSubmitCash} className="space-y-4">
            <Select
              label="Select Event"
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              required
            >
              {events.map((evt) => (
                <option key={evt.event_id} value={evt.event_id}>
                  {evt.event_name}
                </option>
              ))}
            </Select>

            {user?.role === "admin" && (
              <Select
                label="Assigning Collector"
                value={collectorId}
                onChange={(e) => setCollectorId(e.target.value)}
              >
                <option value="">-- Current Collector Shift --</option>
                {collectors.map((col) => (
                  <option key={col.collector_id} value={col.collector_id}>
                    {col.name} ({col.collector_id})
                  </option>
                ))}
              </Select>
            )}

            <Input
              label="Counted Cash Amount (INR)"
              type="number"
              step="0.01"
              placeholder="e.g. 49500.00"
              value={actualCash}
              onChange={(e) => setActualCash(e.target.value)}
              required
            />

            <Input
              label="Explanation (Required if drawer differs from expected system cash)"
              placeholder="e.g. Shortage of change given at entrance"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />

            <div className="pt-3 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setSubmitModalOpen(false)}>
                Cancel
              </Button>
              <ShinyButton type="submit" loading={submitting}>
                Submit For Admin Verification
              </ShinyButton>
            </div>
          </form>
        </Modal>

        {/* Resolve Mismatch Modal */}
        <Modal
          isOpen={resolveModalOpen}
          onClose={() => setResolveModalOpen(false)}
          title="Resolve Cash Discrepancy"
          description={`Reconciliation ID: ${activeRecord?.reconciliation_id}`}
          maxWidth="sm"
        >
          <form onSubmit={handleResolve} className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Difference Variance:</span>
                <span className="font-bold text-rose-400">
                  {formatCurrency(activeRecord?.difference)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Collector Reason:</span>
                <span>{activeRecord?.reason || "None declared"}</span>
              </div>
            </div>

            <Input
              label="Admin Settlement Notes"
              placeholder="e.g. Cash disparity accepted and reconciled into ledger"
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
              required
            />

            <div className="pt-3 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setResolveModalOpen(false)}>
                Cancel
              </Button>
              <ShinyButton type="submit" loading={submitting}>
                Confirm Settlement
              </ShinyButton>
            </div>
          </form>
        </Modal>
      </div>
    </AppShell>
  );
}
