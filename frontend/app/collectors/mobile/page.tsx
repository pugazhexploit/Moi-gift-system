"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyButton } from "@/components/ui/ShinyButton";
import { ShinyText } from "@/components/ui/ShinyText";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { QRCodeView } from "@/components/ui/QRCodeView";
import { useToast } from "@/components/ui/Toast";
import { api } from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { Event, Guest, Transaction } from "@/types/api";
import {
  QrCode,
  Search,
  CheckCircle2,
  Receipt as ReceiptIcon,
  Banknote,
  Globe,
  ArrowRight,
  Sparkles,
  User,
  ShieldCheck,
  RefreshCw,
  LogOut,
  ChevronLeft,
} from "lucide-react";

export default function MobileCollectorPage() {
  const { user, logout } = useAuth();
  const { toast } = useToast();

  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>("");

  // Search & Guest Profile
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Guest[]>([]);
  const [selectedGuest, setSelectedGuest] = useState<Guest | null>(null);

  // Amount & Method
  const [amount, setAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<"cash" | "upi">("cash");
  const [referenceNumber, setReferenceNumber] = useState("");
  const [notes, setNotes] = useState("");

  // State
  const [submitting, setSubmitting] = useState(false);
  const [lastReceipt, setLastReceipt] = useState<any | null>(null);
  const [receiptModalOpen, setReceiptModalOpen] = useState(false);
  const [scanModalOpen, setScanModalOpen] = useState(false);
  const [scanToken, setScanToken] = useState("");

  // Load events
  useEffect(() => {
    api.get<{ items: Event[] }>("/api/events?limit=50").then((res) => {
      if (res.data?.items?.length) {
        setEvents(res.data.items);
        setSelectedEventId(res.data.items[0].event_id);
      }
    });
  }, []);

  // Search guests
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(() => {
      api
        .get<{ items: Guest[] }>(
          `/api/guests?search=${encodeURIComponent(searchQuery)}&event_id=${selectedEventId}`
        )
        .then((res) => {
          if (res.data?.items) setSearchResults(res.data.items);
        });
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, selectedEventId]);

  const handleScanLookup = async () => {
    if (!scanToken.trim()) return;
    try {
      const res = await api.get<Guest>(`/api/guests/scan/${scanToken.trim()}`);
      if (res.data) {
        setSelectedGuest(res.data);
        setScanModalOpen(false);
        setScanToken("");
        toast(`Guest identified: ${res.data.full_name}`);
      }
    } catch (err: any) {
      toast(err?.message || "Invalid or unassigned QR code", "error");
    }
  };

  const handleAddPreset = (val: number) => {
    const current = parseFloat(amount) || 0;
    setAmount((current + val).toString());
  };

  const handleSubmitContribution = async () => {
    if (!selectedGuest) {
      toast("Please select or scan a guest first", "error");
      return;
    }
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      toast("Please enter a valid amount", "error");
      return;
    }

    setSubmitting(true);
    try {
      const idempotencyKey = `mob-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const res = await api.post<any>(
        "/api/transactions",
        {
          event_id: selectedEventId,
          guest_id: selectedGuest.guest_id,
          amount: numAmount.toFixed(2),
          currency: "INR",
          payment_method: paymentMethod,
          reference_number: paymentMethod === "upi" ? referenceNumber || "UPI-DIRECT" : null,
          notes: notes || undefined,
        },
        { "Idempotency-Key": idempotencyKey }
      );

      if (res.data) {
        toast("Contribution recorded successfully!");
        setLastReceipt(res.data);
        setReceiptModalOpen(true);
        // Reset form
        setAmount("");
        setReferenceNumber("");
        setNotes("");
        setSelectedGuest(null);
        setSearchQuery("");
      }
    } catch (err: any) {
      toast(err?.message || "Failed to record contribution", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col max-w-md mx-auto relative overflow-x-hidden">
      {/* Mobile Top App Bar */}
      <header className="p-4 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight">
              <ShinyText>Collector Terminal</ShinyText>
            </h1>
            <p className="text-[10px] text-slate-400">
              {user?.username} ({user?.role})
            </p>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => logout()}
          className="text-slate-400 hover:text-rose-400 p-2"
        >
          <LogOut className="w-4 h-4" />
        </Button>
      </header>

      {/* Event Selector */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-900/40">
        <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
          Active Event
        </label>
        <select
          value={selectedEventId}
          onChange={(e) => {
            setSelectedEventId(e.target.value);
            setSelectedGuest(null);
          }}
          className="w-full text-xs font-semibold rounded-xl bg-slate-900 border border-slate-700 px-3 py-2.5 text-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {events.map((evt) => (
            <option key={evt.event_id} value={evt.event_id}>
              {evt.event_name}
            </option>
          ))}
        </select>
      </div>

      <main className="flex-1 p-4 space-y-4 pb-20">
        {/* Step 1: Identify Guest */}
        {!selectedGuest ? (
          <SpotlightCard className="p-5 border-slate-800 bg-slate-900/80">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Step 1: Identify Guest
            </h2>

            <div className="flex gap-2 mb-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="Search guest name or phone..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <Button
                variant="primary"
                onClick={() => setScanModalOpen(true)}
                className="px-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500"
              >
                <QrCode className="w-4 h-4" />
              </Button>
            </div>

            {/* Live Search Results */}
            {searchResults.length > 0 && (
              <div className="space-y-1.5 max-h-48 overflow-y-auto mt-2 border-t border-slate-800 pt-2">
                {searchResults.map((g) => (
                  <button
                    key={g.guest_id}
                    onClick={() => {
                      setSelectedGuest(g);
                      setSearchResults([]);
                    }}
                    className="w-full text-left p-2.5 rounded-xl hover:bg-slate-800 transition-colors flex items-center justify-between border border-transparent hover:border-slate-700"
                  >
                    <div>
                      <p className="text-xs font-bold text-white">{g.full_name}</p>
                      <p className="text-[10px] text-slate-400">
                        {g.phone} • {g.relationship}
                      </p>
                    </div>
                    <Badge variant="neutral">{g.guest_id}</Badge>
                  </button>
                ))}
              </div>
            )}
          </SpotlightCard>
        ) : (
          /* Guest Profile Preview */
          <div className="p-4 rounded-2xl bg-indigo-950/40 border border-indigo-500/30 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">{selectedGuest.full_name}</span>
                <Badge variant="info">{selectedGuest.guest_id}</Badge>
              </div>
              <p className="text-xs text-indigo-300 mt-0.5">
                {selectedGuest.phone} • {selectedGuest.relationship}
              </p>
            </div>
            <button
              onClick={() => setSelectedGuest(null)}
              className="text-xs text-slate-400 hover:text-white underline p-1"
            >
              Change
            </button>
          </div>
        )}

        {/* Step 2: Monetary Contribution */}
        <SpotlightCard className="p-5 border-slate-800 bg-slate-900/80">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Step 2: Enter Amount & Method
          </h2>

          {/* Amount Display */}
          <div className="relative mb-3">
            <span className="absolute left-4 top-3 text-lg font-bold text-indigo-400">₹</span>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="w-full pl-9 pr-4 py-2.5 rounded-2xl bg-slate-950 border border-slate-800 text-2xl font-bold text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Quick Presets */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[501, 1001, 2001, 5001, 10001, 25000].map((val) => (
              <button
                key={val}
                type="button"
                onClick={() => setAmount(val.toString())}
                className="py-2 text-xs font-semibold rounded-xl bg-slate-800/80 border border-slate-700/80 text-slate-200 hover:bg-indigo-600 hover:text-white hover:border-transparent transition-all active:scale-95"
              >
                ₹{val}
              </button>
            ))}
          </div>

          {/* Payment Method Switcher */}
          <div className="grid grid-cols-2 gap-2 mb-4">
            <button
              type="button"
              onClick={() => setPaymentMethod("cash")}
              className={`flex items-center justify-center gap-2 py-3 rounded-xl border text-xs font-bold transition-all ${
                paymentMethod === "cash"
                  ? "bg-emerald-950/60 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-950"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800"
              }`}
            >
              <Banknote className="w-4 h-4" />
              <span>Cash Envelopes</span>
            </button>

            <button
              type="button"
              onClick={() => setPaymentMethod("upi")}
              className={`flex items-center justify-center gap-2 py-3 rounded-xl border text-xs font-bold transition-all ${
                paymentMethod === "upi"
                  ? "bg-sky-950/60 border-sky-500 text-sky-300 shadow-md shadow-sky-950"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800"
              }`}
            >
              <Globe className="w-4 h-4" />
              <span>UPI / QR Transfer</span>
            </button>
          </div>

          {/* Reference Number if UPI */}
          {paymentMethod === "upi" && (
            <div className="mb-3">
              <Input
                placeholder="UPI Reference No (Optional)"
                value={referenceNumber}
                onChange={(e) => setReferenceNumber(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs py-2"
              />
            </div>
          )}

          {/* Submit Action */}
          <ShinyButton
            type="button"
            onClick={handleSubmitContribution}
            loading={submitting}
            disabled={!selectedGuest || !amount || parseFloat(amount) <= 0}
            className="w-full py-3.5 text-sm font-bold rounded-2xl"
          >
            Confirm & Print Receipt
          </ShinyButton>
        </SpotlightCard>
      </main>

      {/* QR Code Scan / Input Modal */}
      <Modal
        isOpen={scanModalOpen}
        onClose={() => setScanModalOpen(false)}
        title="Guest QR Code Identification"
        description="Scan or enter guest unique QR token"
      >
        <div className="space-y-4 text-center">
          <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 mx-auto flex items-center justify-center">
            <QrCode className="w-8 h-8" />
          </div>

          <Input
            placeholder="Paste or enter QR token uuid..."
            value={scanToken}
            onChange={(e) => setScanToken(e.target.value)}
            className="bg-slate-950 border-slate-800"
          />

          <Button
            onClick={handleScanLookup}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl"
          >
            Lookup Guest
          </Button>
        </div>
      </Modal>

      {/* Receipt Preview Modal */}
      <Modal
        isOpen={receiptModalOpen}
        onClose={() => setReceiptModalOpen(false)}
        title="Contribution Receipt"
        description="Verified financial record generated"
      >
        {lastReceipt && (
          <div className="space-y-4 text-center">
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-left space-y-2 text-xs">
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">Transaction ID:</span>
                <span className="font-bold text-white">
                  {lastReceipt.transaction?.transaction_id}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">Receipt ID:</span>
                <span className="font-bold text-indigo-400">
                  {lastReceipt.receipt?.receipt_id}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">Amount Received:</span>
                <span className="font-bold text-emerald-400 text-base">
                  {formatCurrency(lastReceipt.transaction?.amount)}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">Payment Mode:</span>
                <span className="uppercase font-semibold">
                  {lastReceipt.transaction?.payment_method}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Issued Timestamp:</span>
                <span>{formatDateTime(lastReceipt.receipt?.issued_at)}</span>
              </div>
            </div>

            {/* Verification QR */}
            {lastReceipt.receipt?.verification_token && (
              <div className="pt-2">
                <QRCodeView
                  value={lastReceipt.receipt.verification_token}
                  size={150}
                />
                <p className="text-[10px] text-slate-400 mt-2">
                  Tamper-proof digital verification token
                </p>
              </div>
            )}

            <Button
              onClick={() => {
                window.print();
              }}
              variant="outline"
              className="w-full rounded-xl"
            >
              Print Receipt
            </Button>
          </div>
        )}
      </Modal>
    </div>
  );
}
