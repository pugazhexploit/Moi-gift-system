"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyButton } from "@/components/ui/ShinyButton";
import { ShinyText } from "@/components/ui/ShinyText";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { AuditLog } from "@/types/api";
import { ShieldCheck, Eye, Terminal, RefreshCw } from "lucide-react";

export default function AuditLogsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAction, setSelectedAction] = useState("");
  const [activeLog, setActiveLog] = useState<AuditLog | null>(null);

  const loadLogs = async () => {
    setLoading(true);
    try {
      let url = "/api/audit-logs?limit=50";
      if (selectedAction) url += `&action=${selectedAction}`;
      const res = await api.get<{ items: AuditLog[] }>(url);
      if (res.data?.items) setLogs(res.data.items);
    } catch (err: any) {
      toast(err?.message || "Failed to load audit logs", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [selectedAction]);

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <ShinyText>Immutable Audit Trail</ShinyText>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Append-only cryptographic security trail recording all administrative and financial mutations.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={loadLogs}
            className="rounded-xl"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Trail
          </Button>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-3">
          <select
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value)}
            className="text-xs font-medium rounded-xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-slate-800 dark:text-slate-200"
          >
            <option value="">All Security Actions</option>
            <option value="LOGIN">LOGIN</option>
            <option value="CREATE">CREATE</option>
            <option value="UPDATE">UPDATE</option>
            <option value="VERIFY">VERIFY</option>
            <option value="REJECT">REJECT</option>
            <option value="LOCK">LOCK</option>
            <option value="ROLE_CHANGE">ROLE_CHANGE</option>
            <option value="PASSWORD_CHANGE">PASSWORD_CHANGE</option>
          </select>
        </div>

        {/* Logs Table */}
        <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200/80 dark:border-slate-800/80">
                <tr>
                  <th className="p-3.5">Timestamp</th>
                  <th className="p-3.5">Action</th>
                  <th className="p-3.5">Entity</th>
                  <th className="p-3.5">IP Address</th>
                  <th className="p-3.5">Request ID</th>
                  <th className="p-3.5 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5 text-slate-400">{formatDateTime(log.timestamp)}</td>
                    <td className="p-3.5">
                      <Badge
                        variant={
                          log.action === "LOCK"
                            ? "purple"
                            : log.action === "VERIFY"
                            ? "success"
                            : log.action === "CREATE"
                            ? "info"
                            : "neutral"
                        }
                      >
                        {log.action}
                      </Badge>
                    </td>
                    <td className="p-3.5 font-medium capitalize">
                      {log.entity_type} {log.entity_id ? `(${log.entity_id})` : ""}
                    </td>
                    <td className="p-3.5 font-mono">{log.ip_address || "Internal"}</td>
                    <td className="p-3.5 font-mono text-[11px] text-slate-500 truncate max-w-[120px]">
                      {log.request_id || "-"}
                    </td>
                    <td className="p-3.5 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setActiveLog(log)}
                        className="py-1 px-2 text-xs"
                      >
                        <Eye className="w-3.5 h-3.5 text-indigo-400 mr-1" />
                        Payload
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {logs.length === 0 && !loading && (
            <div className="p-8 text-center text-xs text-slate-400">
              No audit logs recorded for this action.
            </div>
          )}
        </div>

        {/* Payload Detail Modal */}
        <Modal
          isOpen={!!activeLog}
          onClose={() => setActiveLog(null)}
          title="Audit Trail Mutation Payload"
          description={`Action: ${activeLog?.action} on ${activeLog?.entity_type}`}
          maxWidth="lg"
        >
          {activeLog && (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Old State
                </p>
                <pre className="p-3 rounded-xl bg-slate-950 text-slate-300 font-mono text-xs overflow-x-auto border border-slate-800">
                  {JSON.stringify(activeLog.old_value, null, 2)}
                </pre>
              </div>

              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  New State
                </p>
                <pre className="p-3 rounded-xl bg-slate-950 text-emerald-400 font-mono text-xs overflow-x-auto border border-slate-800">
                  {JSON.stringify(activeLog.new_value, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </AppShell>
  );
}
