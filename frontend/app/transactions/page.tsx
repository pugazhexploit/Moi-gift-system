"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyButton } from "@/components/ui/ShinyButton";
import { ShinyText } from "@/components/ui/ShinyText";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { QRCodeView } from "@/components/ui/QRCodeView";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { Transaction, Event, TransactionStatus, PaymentMethod } from "@/types/api";
import {
  CreditCard,
  CheckCircle2,
  XCircle,
  Lock,
  Receipt,
  Filter,
  RefreshCw,
  Banknote,
  Globe,
  Printer,
} from "lucide-react";

export default function TransactionsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const [selectedMethod, setSelectedMethod] = useState<string>("");
  const [loading, setLoading] = useState(true);

  // Modals
  const [receiptModalOpen, setReceiptModalOpen] = useState(false);
  const [selectedReceipt, setSelectedReceipt] = useState<any | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const evtRes = await api.get<{ items: Event[] }>("/api/events?limit=50");
      if (evtRes.data?.items) setEvents(evtRes.data.items);

      let url = "/api/transactions?limit=100";
      if (selectedEventId) url += `&event_id=${selectedEventId}`;
      if (selectedStatus) url += `&status=${selectedStatus}`;
      if (selectedMethod) url += `&payment_method=${selectedMethod}`;

      const res = await api.get<{ items: Transaction[] }>(url);
      if (res.data?.items) setTransactions(res.data.items);
    } catch (err: any) {
      toast(err?.message || "Failed to load transactions", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedEventId, selectedStatus, selectedMethod]);

  const handleAction = async (txnId: string, action: "verify" | "reject" | "lock") => {
    setActionLoading(txnId);
    try {
      await api.post(`/api/transactions/${txnId}/${action}`, { notes: `Admin ${action} action` });
      toast(`Transaction ${txnId} marked as ${action}ed`);
      loadData();
    } catch (err: any) {
      toast(err?.message || `Failed to ${action} transaction`, "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewReceipt = async (txn: Transaction) => {
    try {
      // Find or fetch receipt by transaction
      const res = await api.get<any>(`/api/receipts/${txn.transaction_id.replace("TXN", "RCP")}`);
      if (res.data) {
        setSelectedReceipt({ ...res.data, transaction: txn });
        setReceiptModalOpen(true);
      }
    } catch {
      // Fallback display
      setSelectedReceipt({ transaction: txn, receipt: { receipt_id: txn.transaction_id.replace("TXN", "RCP"), issued_at: txn.created_at } });
      setReceiptModalOpen(true);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <ShinyText>Financial Ledger & Transactions</ShinyText>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Authoritative transaction records, verification flow and permanent locking.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            className="rounded-xl"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Ledger
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
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

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs font-medium rounded-xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-slate-800 dark:text-slate-200"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="verified">Verified</option>
            <option value="rejected">Rejected</option>
            <option value="locked">Locked</option>
          </select>

          <select
            value={selectedMethod}
            onChange={(e) => setSelectedMethod(e.target.value)}
            className="text-xs font-medium rounded-xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-slate-800 dark:text-slate-200"
          >
            <option value="">All Payment Modes</option>
            <option value="cash">Cash</option>
            <option value="upi">UPI / Online</option>
            <option value="bank_transfer">Bank Transfer</option>
          </select>
        </div>

        {/* Ledger Table */}
        <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200/80 dark:border-slate-800/80">
                <tr>
                  <th className="p-3.5">Txn ID</th>
                  <th className="p-3.5">Amount</th>
                  <th className="p-3.5">Payment Mode</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Collector</th>
                  <th className="p-3.5">Recorded Time</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
                {transactions.map((t) => (
                  <tr key={t.transaction_id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5 font-mono font-medium text-indigo-600 dark:text-indigo-400">
                      {t.transaction_id}
                    </td>
                    <td className="p-3.5 font-bold text-slate-900 dark:text-white text-sm">
                      {formatCurrency(t.amount)}
                    </td>
                    <td className="p-3.5">
                      <div className="inline-flex items-center gap-1.5 capitalize">
                        {t.payment_method === "cash" ? (
                          <Banknote className="w-3.5 h-3.5 text-emerald-500" />
                        ) : (
                          <Globe className="w-3.5 h-3.5 text-sky-500" />
                        )}
                        <span>{t.payment_method}</span>
                      </div>
                    </td>
                    <td className="p-3.5">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="p-3.5 font-mono">{t.collector_id}</td>
                    <td className="p-3.5 text-slate-400">{formatDateTime(t.created_at)}</td>
                    <td className="p-3.5 text-right space-x-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewReceipt(t)}
                        className="py-1 px-2 text-xs"
                      >
                        <Receipt className="w-3.5 h-3.5 text-indigo-500 mr-1" />
                        Receipt
                      </Button>

                      {user?.role === "admin" && t.status === "pending" && (
                        <>
                          <Button
                            variant="success"
                            size="sm"
                            loading={actionLoading === t.transaction_id}
                            onClick={() => handleAction(t.transaction_id, "verify")}
                            className="py-1 px-2 text-xs"
                          >
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Verify
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            loading={actionLoading === t.transaction_id}
                            onClick={() => handleAction(t.transaction_id, "reject")}
                            className="py-1 px-2 text-xs"
                          >
                            <XCircle className="w-3 h-3 mr-1" />
                            Reject
                          </Button>
                        </>
                      )}

                      {user?.role === "admin" && t.status === "verified" && (
                        <Button
                          variant="secondary"
                          size="sm"
                          loading={actionLoading === t.transaction_id}
                          onClick={() => handleAction(t.transaction_id, "lock")}
                          className="py-1 px-2 text-xs bg-purple-950/40 text-purple-300 border border-purple-800/50 hover:bg-purple-900/60"
                        >
                          <Lock className="w-3 h-3 mr-1" />
                          Lock
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {transactions.length === 0 && !loading && (
            <div className="p-8 text-center text-xs text-slate-400">
              No transactions matching the selected filters.
            </div>
          )}
        </div>

        {/* Receipt Modal */}
        <Modal
          isOpen={receiptModalOpen}
          onClose={() => setReceiptModalOpen(false)}
          title="Official Receipt Voucher"
          description="GiftLedger Authorized Financial Proof"
          maxWidth="md"
        >
          {selectedReceipt && (
            <div className="space-y-4 text-center">
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-left space-y-2 text-xs">
                <div className="flex justify-between border-b border-slate-800 pb-2">
                  <span className="text-slate-400">Transaction ID:</span>
                  <span className="font-mono font-bold text-white">
                    {selectedReceipt.transaction?.transaction_id}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-2">
                  <span className="text-slate-400">Receipt ID:</span>
                  <span className="font-mono font-bold text-indigo-400">
                    {selectedReceipt.receipt?.receipt_id}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-2">
                  <span className="text-slate-400">Amount Received:</span>
                  <span className="font-bold text-emerald-400 text-base">
                    {formatCurrency(selectedReceipt.transaction?.amount)}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-2">
                  <span className="text-slate-400">Payment Mode:</span>
                  <span className="uppercase font-semibold text-white">
                    {selectedReceipt.transaction?.payment_method}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-2">
                  <span className="text-slate-400">Collector:</span>
                  <span className="font-mono">{selectedReceipt.transaction?.collector_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Timestamp:</span>
                  <span>{formatDateTime(selectedReceipt.transaction?.created_at)}</span>
                </div>
              </div>

              {selectedReceipt.receipt?.verification_token && (
                <div className="pt-2">
                  <QRCodeView
                    value={selectedReceipt.receipt.verification_token}
                    size={140}
                  />
                  <p className="text-[10px] text-slate-400 mt-1">
                    Digital verification QR stamp
                  </p>
                </div>
              )}

              <Button
                variant="outline"
                onClick={() => window.print()}
                className="w-full text-xs rounded-xl"
              >
                <Printer className="w-3.5 h-3.5 mr-1" />
                Print Voucher
              </Button>
            </div>
          )}
        </Modal>
      </div>
    </AppShell>
  );
}
