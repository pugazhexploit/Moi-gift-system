"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyButton } from "@/components/ui/ShinyButton";
import { ShinyText } from "@/components/ui/ShinyText";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { Gift, GiftType, Event, Guest } from "@/types/api";
import { Gift as GiftIcon, Plus, Filter, Package, Tag } from "lucide-react";

export default function GiftsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [gifts, setGifts] = useState<Gift[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [guests, setGuests] = useState<Guest[]>([]);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [loading, setLoading] = useState(true);

  // Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form
  const [guestId, setGuestId] = useState("");
  const [giftType, setGiftType] = useState<GiftType>("household_item");
  const [description, setDescription] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [estimatedValue, setEstimatedValue] = useState("");
  const [notes, setNotes] = useState("");

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

      let url = "/api/gifts?limit=100";
      if (selectedEventId) url += `&event_id=${selectedEventId}`;
      const res = await api.get<{ items: Gift[] }>(url);
      if (res.data?.items) setGifts(res.data.items);
    } catch (err: any) {
      toast(err?.message || "Failed to load gifts", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedEventId]);

  useEffect(() => {
    if (selectedEventId) {
      api.get<{ items: Guest[] }>(`/api/guests?event_id=${selectedEventId}&limit=100`).then((res) => {
        if (res.data?.items) setGuests(res.data.items);
      });
    }
  }, [selectedEventId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventId || !guestId || !description) {
      toast("Event, guest, and description are required", "error");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/gifts", {
        event_id: selectedEventId,
        guest_id: guestId,
        gift_type: giftType,
        description,
        quantity: Number(quantity),
        estimated_value: estimatedValue ? parseFloat(estimatedValue).toFixed(2) : undefined,
        notes: notes || undefined,
      });
      toast("Gift catalogued successfully!");
      setCreateModalOpen(false);
      setDescription("");
      setQuantity(1);
      setEstimatedValue("");
      setNotes("");
      loadData();
    } catch (err: any) {
      toast(err?.message || "Failed to record gift", "error");
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
              <ShinyText>Physical Gifts & Presents Registry</ShinyText>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Catalog and inventory non-monetary wedding and ceremony items with optional valuation.
            </p>
          </div>

          <ShinyButton
            onClick={() => setCreateModalOpen(true)}
            className="py-2.5 px-4 text-xs font-semibold rounded-xl"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Record Physical Gift
          </ShinyButton>
        </div>

        {/* Filter */}
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

        {/* Gifts Table */}
        <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200/80 dark:border-slate-800/80">
                <tr>
                  <th className="p-3.5">Gift ID</th>
                  <th className="p-3.5">Item Description</th>
                  <th className="p-3.5">Category</th>
                  <th className="p-3.5">Qty</th>
                  <th className="p-3.5">Estimated Value</th>
                  <th className="p-3.5">Collector</th>
                  <th className="p-3.5">Logged At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
                {gifts.map((g) => (
                  <tr key={g.gift_id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5 font-mono font-medium text-rose-500">
                      {g.gift_id}
                    </td>
                    <td className="p-3.5 font-semibold text-slate-900 dark:text-white">
                      {g.description}
                    </td>
                    <td className="p-3.5">
                      <Badge variant="purple" className="capitalize">
                        {g.gift_type.replace("_", " ")}
                      </Badge>
                    </td>
                    <td className="p-3.5 font-bold">{g.quantity}</td>
                    <td className="p-3.5 font-medium text-slate-900 dark:text-white">
                      {g.estimated_value ? formatCurrency(g.estimated_value) : "Not specified"}
                    </td>
                    <td className="p-3.5 font-mono">{g.collector_id}</td>
                    <td className="p-3.5 text-slate-400">{formatDateTime(g.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {gifts.length === 0 && !loading && (
            <div className="p-8 text-center text-xs text-slate-400">
              No physical gifts catalogued for this event yet.
            </div>
          )}
        </div>

        {/* Record Gift Modal */}
        <Modal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Catalog Physical Gift"
          description="Log non-cash presents delivered to the reception"
          maxWidth="md"
        >
          <form onSubmit={handleCreate} className="space-y-4">
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

            <Select
              label="Select Gifting Guest"
              value={guestId}
              onChange={(e) => setGuestId(e.target.value)}
              required
            >
              <option value="">-- Choose Guest --</option>
              {guests.map((gst) => (
                <option key={gst.guest_id} value={gst.guest_id}>
                  {gst.full_name} ({gst.guest_id})
                </option>
              ))}
            </Select>

            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Gift Category"
                value={giftType}
                onChange={(e) => setGiftType(e.target.value as GiftType)}
              >
                <option value="household_item">Household Item</option>
                <option value="decorative">Decorative / Idol</option>
                <option value="clothing">Clothing / Saree</option>
                <option value="electronics">Electronics</option>
                <option value="accessories">Jewelry / Accessories</option>
                <option value="other">Other</option>
              </Select>

              <Input
                label="Quantity"
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                required
              />
            </div>

            <Input
              label="Item Description"
              placeholder="e.g. Prestige Mixer Grinder 750W"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            />

            <Input
              label="Estimated Value (Optional - INR)"
              type="number"
              placeholder="3500.00"
              value={estimatedValue}
              onChange={(e) => setEstimatedValue(e.target.value)}
            />

            <Input
              label="Notes / Packaging"
              placeholder="Delivered with gift wrap..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />

            <div className="pt-3 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                Cancel
              </Button>
              <ShinyButton type="submit" loading={submitting}>
                Save Gift Record
              </ShinyButton>
            </div>
          </form>
        </Modal>
      </div>
    </AppShell>
  );
}
