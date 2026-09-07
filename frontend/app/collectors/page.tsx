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
import { Collector, Event, User } from "@/types/api";
import { UserCheck, Plus, Link as LinkIcon, Phone, User as UserIcon } from "lucide-react";

export default function CollectorsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [collectors, setCollectors] = useState<Collector[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [selectedCollector, setSelectedCollector] = useState<Collector | null>(null);
  const [assignEventId, setAssignEventId] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Form
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [selectedUserId, setSelectedUserId] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.get<{ items: Collector[] }>("/api/collectors?limit=50");
      if (res.data?.items) setCollectors(res.data.items);

      const evtRes = await api.get<{ items: Event[] }>("/api/events?limit=50");
      if (evtRes.data?.items) setEvents(evtRes.data.items);

      const usrRes = await api.get<{ items: User[] }>("/api/users?role=collector&limit=50");
      if (usrRes.data?.items) setUsers(usrRes.data.items);
    } catch (err: any) {
      toast(err?.message || "Failed to load collectors", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !phone || !employeeCode || !selectedUserId) {
      toast("All fields are required", "error");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/collectors", {
        user_id: selectedUserId,
        name,
        phone,
        employee_code: employeeCode,
      });
      toast("Collector profile created!");
      setCreateModalOpen(false);
      setName("");
      setPhone("");
      setEmployeeCode("");
      setSelectedUserId("");
      loadData();
    } catch (err: any) {
      toast(err?.message || "Failed to create collector", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCollector || !assignEventId) return;
    setSubmitting(true);
    try {
      await api.post(`/api/events/${assignEventId}/collectors/${selectedCollector.collector_id}`);
      toast(`Assigned ${selectedCollector.name} to event!`);
      setAssignModalOpen(false);
    } catch (err: any) {
      toast(err?.message || "Failed to assign collector", "error");
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
              <ShinyText>Collection Staff & Authorizations</ShinyText>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Authorized personnel credentials, employee tracking, and event assignments.
            </p>
          </div>

          <ShinyButton
            onClick={() => setCreateModalOpen(true)}
            className="py-2.5 px-4 text-xs font-semibold rounded-xl"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Add Collector Profile
          </ShinyButton>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {collectors.map((col) => (
            <SpotlightCard key={col.collector_id} className="p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
                    <UserIcon className="w-5 h-5" />
                  </div>
                  <StatusBadge status={col.status} />
                </div>

                <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
                  {col.name}
                </h3>
                <p className="text-xs text-indigo-400 font-mono font-medium mb-3">
                  {col.collector_id} • {col.employee_code}
                </p>

                <div className="flex items-center gap-2 text-xs text-slate-400 border-t border-slate-800 pt-3">
                  <Phone className="w-3.5 h-3.5 text-indigo-500" />
                  <span>{col.phone}</span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedCollector(col);
                    setAssignModalOpen(true);
                  }}
                  className="rounded-xl text-xs py-1.5"
                >
                  <LinkIcon className="w-3 h-3 mr-1 text-indigo-400" />
                  Assign to Event
                </Button>
              </div>
            </SpotlightCard>
          ))}
        </div>

        {/* Create Collector Modal */}
        <Modal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          title="Create Collector Profile"
          description="Bind a collector profile to a registered user account"
          maxWidth="md"
        >
          <form onSubmit={handleCreate} className="space-y-4">
            <Select
              label="Select Collector Account"
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              required
            >
              <option value="">-- Choose User Account --</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.username} ({u.email})
                </option>
              ))}
            </Select>

            <Input
              label="Full Name"
              placeholder="e.g. Ramesh Collector"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />

            <Input
              label="Phone Number"
              placeholder="+919876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />

            <Input
              label="Employee / Staff Code"
              placeholder="EMP-101"
              value={employeeCode}
              onChange={(e) => setEmployeeCode(e.target.value)}
              required
            />

            <div className="pt-3 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                Cancel
              </Button>
              <ShinyButton type="submit" loading={submitting}>
                Save Profile
              </ShinyButton>
            </div>
          </form>
        </Modal>

        {/* Assign Modal */}
        <Modal
          isOpen={assignModalOpen}
          onClose={() => setAssignModalOpen(false)}
          title={`Assign ${selectedCollector?.name || "Collector"}`}
          description="Grant permission to record contributions for this gathering"
          maxWidth="sm"
        >
          <form onSubmit={handleAssign} className="space-y-4">
            <Select
              label="Select Event"
              value={assignEventId}
              onChange={(e) => setAssignEventId(e.target.value)}
              required
            >
              <option value="">-- Choose Event --</option>
              {events.map((evt) => (
                <option key={evt.event_id} value={evt.event_id}>
                  {evt.event_name}
                </option>
              ))}
            </Select>

            <div className="pt-3 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setAssignModalOpen(false)}>
                Cancel
              </Button>
              <ShinyButton type="submit" loading={submitting}>
                Confirm Assignment
              </ShinyButton>
            </div>
          </form>
        </Modal>
      </div>
    </AppShell>
  );
}
