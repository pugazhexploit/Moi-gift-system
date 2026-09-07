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
import { formatDate } from "@/lib/utils";
import { Event, EventType, EventStatus } from "@/types/api";
import {
  Calendar,
  Plus,
  Search,
  MapPin,
  Clock,
  ArrowRight,
  Edit2,
  Sparkles,
  PartyPopper,
} from "lucide-react";
import Link from "next/link";

export default function EventsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Direct / Inline Create Event Form State
  const [eventName, setEventName] = useState("");
  const [eventType, setEventType] = useState<EventType>("wedding");
  const [venue, setVenue] = useState("");
  const [eventDate, setEventDate] = useState(new Date().toISOString().split("T")[0]);
  const [startTime, setStartTime] = useState("18:00");
  const [endTime, setEndTime] = useState("23:00");
  const [description, setDescription] = useState("");

  // Edit Event Name Modal State
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [editName, setEditName] = useState("");
  const [editVenue, setEditVenue] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const q = search ? `&search=${encodeURIComponent(search)}` : "";
      const res = await api.get<{ items: Event[] }>(`/api/events?limit=50${q}`);
      if (res.data?.items) {
        setEvents(res.data.items);
      }
    } catch (err: any) {
      toast(err?.message || "Failed to load events", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [search]);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!eventName.trim()) {
      toast("Please enter the Event Name", "error");
      return;
    }
    if (!venue.trim()) {
      toast("Please enter the Venue", "error");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/events", {
        event_name: eventName.trim(),
        event_type: eventType,
        venue: venue.trim(),
        event_date: new Date(eventDate).toISOString(),
        start_time: startTime,
        end_time: endTime,
        description: description || "Celebration gathering",
        status: "active",
      });
      toast(`Event "${eventName}" created successfully!`);
      // Reset form fields
      setEventName("");
      setVenue("");
      setDescription("");
      loadEvents();
    } catch (err: any) {
      toast(err?.message || "Failed to create event", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEvent || !editName.trim()) return;
    setSavingEdit(true);
    try {
      await api.patch(`/api/events/${editingEvent.event_id}`, {
        event_name: editName.trim(),
        venue: editVenue.trim() || undefined,
      });
      toast("Event name updated successfully!");
      setEditingEvent(null);
      loadEvents();
    } catch (err: any) {
      toast(err?.message || "Failed to update event", "error");
    } finally {
      setSavingEdit(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-8">
        {/* Top Header */}
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            <ShinyText>Event Management</ShinyText>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Create, name, and manage celebrations, wedding receptions, and family functions.
          </p>
        </div>

        {/* 1. DIRECT INLINE EVENT CREATOR CARD */}
        <SpotlightCard className="p-6 border-indigo-500/30 bg-slate-900/90 shadow-xl">
          <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-slate-800">
            <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400">
              <PartyPopper className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Enter & Create New Event</h2>
              <p className="text-xs text-slate-400">
                Type the event name below to instantly add it to your ledger
              </p>
            </div>
          </div>

          <form onSubmit={handleCreateEvent} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Event Name Input */}
              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-indigo-300 mb-1.5 uppercase tracking-wider">
                  Event Name (Required) *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Ramesh & Sita Wedding Reception, Anand 50th Birthday..."
                  value={eventName}
                  onChange={(e) => setEventName(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-xl text-sm font-semibold bg-slate-950 border border-indigo-500/50 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-inner"
                />
              </div>

              {/* Event Type */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Event Category
                </label>
                <select
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value as EventType)}
                  className="w-full px-3.5 py-2.5 rounded-xl text-xs font-medium bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="wedding">💍 Wedding</option>
                  <option value="reception">🎉 Reception</option>
                  <option value="birthday">🎂 Birthday</option>
                  <option value="festival">🪔 Festival</option>
                  <option value="temple_event">🛕 Temple Event</option>
                  <option value="family_function">👨‍👩‍👧‍👦 Family Function</option>
                  <option value="community_event">🤝 Community Event</option>
                  <option value="other">✨ Other Celebration</option>
                </select>
              </div>

              {/* Venue */}
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Venue & Hall Location *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Grand Palace Hall, Anna Nagar, Chennai"
                  value={venue}
                  onChange={(e) => setVenue(e.target.value)}
                  required
                  className="w-full px-3.5 py-2 rounded-xl text-xs bg-slate-950 border border-slate-800 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Date */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Event Date *
                </label>
                <input
                  type="date"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                  required
                  className="w-full px-3.5 py-2 rounded-xl text-xs bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-slate-500">
                Created events immediately become available in the Collector Mobile terminal
              </span>
              <ShinyButton type="submit" loading={submitting} className="py-2.5 px-6 text-xs font-bold rounded-xl">
                <Plus className="w-4 h-4 mr-1.5" />
                Add Event
              </ShinyButton>
            </div>
          </form>
        </SpotlightCard>

        {/* 2. SEARCH & EXISTING EVENTS LIST */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Active Events Directory</span>
              <Badge variant="purple">{events.length} Registered</Badge>
            </h2>

            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                placeholder="Search event name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-xl text-xs bg-slate-900 border border-slate-800 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Events Grid with PROMINENT EVENT NAMES */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((evt) => (
              <SpotlightCard
                key={evt.event_id}
                spotlightColor="rgba(99, 102, 241, 0.25)"
                className="p-6 flex flex-col justify-between border-slate-800 bg-slate-900/90"
              >
                <div>
                  {/* Top Bar: Event ID & Status */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-950/60 px-2.5 py-1 rounded-lg border border-indigo-800/50">
                      {evt.event_id}
                    </span>
                    <div className="flex items-center gap-2">
                      <Badge variant="purple" className="uppercase font-bold tracking-wider text-[10px]">
                        {evt.event_type}
                      </Badge>
                      <StatusBadge status={evt.status} />
                    </div>
                  </div>

                  {/* PROMINENT EVENT NAME BANNER */}
                  <div className="p-3.5 rounded-xl bg-slate-950/90 border border-indigo-500/20 mb-3 shadow-inner group">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 block mb-0.5">
                          Event Name
                        </span>
                        <h3 className="text-base font-extrabold text-white leading-tight">
                          {evt.event_name}
                        </h3>
                      </div>
                      <button
                        onClick={() => {
                          setEditingEvent(evt);
                          setEditName(evt.event_name);
                          setEditVenue(evt.venue);
                        }}
                        title="Rename or edit event"
                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-slate-800 transition-colors"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 mb-4 line-clamp-2">
                    {evt.description || "Official gathering and monetary gift collection."}
                  </p>

                  {/* Meta Details */}
                  <div className="space-y-2 text-xs text-slate-300 border-t border-slate-800 pt-3">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                      <span>{formatDate(evt.event_date)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-indigo-400" />
                      <span>{evt.start_time} - {evt.end_time}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="truncate">{evt.venue}</span>
                    </div>
                  </div>
                </div>

                {/* Actions Bottom Bar */}
                <div className="mt-5 pt-4 border-t border-slate-800 flex items-center justify-between">
                  <button
                    onClick={() => {
                      setEditingEvent(evt);
                      setEditName(evt.event_name);
                      setEditVenue(evt.venue);
                    }}
                    className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-medium"
                  >
                    <Edit2 className="w-3 h-3" />
                    Rename
                  </button>

                  <Link
                    href={`/dashboard?event_id=${evt.event_id}`}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 bg-indigo-950/60 hover:bg-indigo-900/60 px-3 py-1.5 rounded-xl border border-indigo-800/50 transition-all"
                  >
                    <span>View Financials</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </SpotlightCard>
            ))}
          </div>

          {events.length === 0 && !loading && (
            <div className="p-12 text-center text-xs text-slate-400 border border-dashed border-slate-800 rounded-2xl">
              No events found. Use the form above to create your first event!
            </div>
          )}
        </div>

        {/* Edit Event Name Modal */}
        <Modal
          isOpen={!!editingEvent}
          onClose={() => setEditingEvent(null)}
          title="Edit Event Name"
          description={`Update details for ${editingEvent?.event_id}`}
          maxWidth="md"
        >
          <form onSubmit={handleSaveEdit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-indigo-300 mb-1.5 uppercase">
                Event Name
              </label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 rounded-xl text-sm font-semibold bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Venue Location
              </label>
              <input
                type="text"
                value={editVenue}
                onChange={(e) => setEditVenue(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl text-xs bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="pt-3 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setEditingEvent(null)}>
                Cancel
              </Button>
              <ShinyButton type="submit" loading={savingEdit}>
                Update Event Name
              </ShinyButton>
            </div>
          </form>
        </Modal>
      </div>
    </AppShell>
  );
}
