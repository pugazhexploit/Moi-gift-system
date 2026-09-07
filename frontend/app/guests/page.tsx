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
import { QRCodeView } from "@/components/ui/QRCodeView";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { Guest, Event } from "@/types/api";
import { Users, Plus, Search, QrCode, Phone, MapPin, Eye, Copy } from "lucide-react";

export default function GuestsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [guests, setGuests] = useState<Guest[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [qrModalOpen, setQrModalOpen] = useState(false);
  const [activeQrGuest, setActiveQrGuest] = useState<any | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [relationship, setRelationship] = useState("");
  const [familyName, setFamilyName] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("Tamil Nadu");
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

      const q = search ? `&search=${encodeURIComponent(search)}` : "";
      const evtQuery = selectedEventId ? `&event_id=${selectedEventId}` : "";
      const res = await api.get<{ items: Guest[] }>(`/api/guests?limit=100${q}${evtQuery}`);
      if (res.data?.items) setGuests(res.data.items);
    } catch (err: any) {
      toast(err?.message || "Failed to load guests", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [search, selectedEventId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !phone || !selectedEventId) {
      toast("Name, phone, and event are required", "error");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/guests", {
        event_id: selectedEventId,
        full_name: fullName,
        phone,
        email: email || undefined,
        relationship: relationship || "Guest",
        family_name: familyName || "General",
        address: {
          line_1: city ? `${city} Main Rd` : "Address Line 1",
          city: city || "Chennai",
          state: state || "Tamil Nadu",
          postal_code: "600001",
          country: "India",
        },
        notes: notes || undefined,
      });
      toast("Guest registered successfully!");
      setCreateModalOpen(false);
      // Reset
      setFullName("");
      setPhone("");
      setEmail("");
      setRelationship("");
      setFamilyName("");
      setCity("");
      setNotes("");
      loadData();
    } catch (err: any) {
      toast(err?.message || "Failed to register guest", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewQr = async (guest: Guest) => {
    try {
      const res = await api.get<any>(`/api/guests/${guest.guest_id}/qr`);
      if (res.data) {
        setActiveQrGuest({ ...guest, ...res.data });
        setQrModalOpen(true);
      }
    } catch (err: any) {
      toast(err?.message || "Failed to load QR code", "error");
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <ShinyText>Guest Management</ShinyText>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Directory of attendees with QR tokens, contact details and contribution profiles.
            </p>
          </div>

          <ShinyButton
            onClick={() => setCreateModalOpen(true)}
            className="py-2.5 px-4 text-xs font-semibold rounded-xl"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Register Guest
          </ShinyButton>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search by name, phone, family name, or Guest ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

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

        {/* Guests Table */}
        <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200/80 dark:border-slate-800/80">
                <tr>
                  <th className="p-3.5">Guest ID</th>
                  <th className="p-3.5">Full Name</th>
                  <th className="p-3.5">Contact</th>
                  <th className="p-3.5">Relationship</th>
                  <th className="p-3.5">Family Group</th>
                  <th className="p-3.5">City</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
                {guests.map((g) => (
                  <tr key={g.guest_id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5 font-mono font-medium text-indigo-600 dark:text-indigo-400">
                      {g.guest_id}
                    </td>
                    <td className="p-3.5 font-semibold text-slate-900 dark:text-white">
                      {g.full_name}
                    </td>
                    <td className="p-3.5">
                      <div className="flex items-center gap-1.5">
                        <Phone className="w-3 h-3 text-slate-400" />
                        <span>{g.phone}</span>
                      </div>
                    </td>
                    <td className="p-3.5">
                      <Badge variant="neutral">{g.relationship || "Guest"}</Badge>
                    </td>
                    <td className="p-3.5 font-medium">{g.family_name || "-"}</td>
                    <td className="p-3.5">{g.address?.city || "-"}</td>
                    <td className="p-3.5 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewQr(g)}
                        className="py-1 px-2.5 rounded-lg text-xs"
                      >
                        <QrCode className="w-3.5 h-3.5 mr-1 text-indigo-500" />
                        QR Code
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {guests.length === 0 && !loading && (
            <div className="p-8 text-center text-xs text-slate-400">
              No guests found. Register a guest to generate their personalized QR badge.
            </div>
          )}
        </div>

        {/* Register Guest Modal */}
        <Modal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Register New Guest"
          description="Add guest details and auto-generate privacy-preserving QR code"
          maxWidth="lg"
        >
          <form onSubmit={handleCreate} className="space-y-4">
            <Select
              label="Assigned Event"
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

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Full Name"
                placeholder="e.g. Ramesh Iyer"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
              <Input
                label="Phone Number"
                placeholder="+919876543210"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Relationship"
                placeholder="e.g. Groom Friend, Cousin"
                value={relationship}
                onChange={(e) => setRelationship(e.target.value)}
              />
              <Input
                label="Family Group"
                placeholder="e.g. Iyer Family"
                value={familyName}
                onChange={(e) => setFamilyName(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="City / Town"
                placeholder="Chennai"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
              <Input
                label="State"
                placeholder="Tamil Nadu"
                value={state}
                onChange={(e) => setState(e.target.value)}
              />
            </div>

            <Input
              label="Special Notes"
              placeholder="VIP seat, dietary preference, etc."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />

            <div className="pt-3 flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateModalOpen(false)}
              >
                Cancel
              </Button>
              <ShinyButton type="submit" loading={submitting}>
                Save & Issue QR Badge
              </ShinyButton>
            </div>
          </form>
        </Modal>

        {/* QR Code Modal */}
        <Modal
          isOpen={qrModalOpen}
          onClose={() => setQrModalOpen(false)}
          title="Guest Digital Badge"
          description={activeQrGuest?.full_name || ""}
          maxWidth="sm"
        >
          {activeQrGuest && (
            <div className="text-center space-y-4">
              <div className="p-3 bg-white dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 inline-block shadow-lg">
                <QRCodeView value={activeQrGuest.qr_token || activeQrGuest.guest_id} size={180} />
              </div>

              <div className="text-xs space-y-1">
                <p className="font-mono text-indigo-400 font-bold">{activeQrGuest.guest_id}</p>
                <p className="text-slate-400">{activeQrGuest.phone}</p>
                <p className="text-[11px] text-slate-500">
                  Relationship: {activeQrGuest.relationship}
                </p>
              </div>

              <Button
                variant="outline"
                className="w-full text-xs rounded-xl"
                onClick={() => {
                  navigator.clipboard.writeText(activeQrGuest.qr_token || "");
                  toast("Token copied to clipboard!");
                }}
              >
                <Copy className="w-3.5 h-3.5 mr-1" />
                Copy QR Token
              </Button>
            </div>
          )}
        </Modal>
      </div>
    </AppShell>
  );
}
