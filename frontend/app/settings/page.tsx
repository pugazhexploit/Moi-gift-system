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
import { formatDateTime } from "@/lib/utils";
import { User, UserRole, UserStatus } from "@/types/api";
import { Shield, KeyRound, UserPlus, Users, Lock } from "lucide-react";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { toast } = useToast();

  // Password Change
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPass, setChangingPass] = useState(false);

  // Admin User Management
  const [users, setUsers] = useState<User[]>([]);
  const [createUserModalOpen, setCreateUserModalOpen] = useState(false);
  const [submittingUser, setSubmittingUser] = useState(false);

  // New User Form
  const [newUsername, setNewUsername] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newUserPass, setNewUserPass] = useState("");
  const [newUserRole, setNewUserRole] = useState<UserRole>("collector");

  const loadUsers = async () => {
    if (user?.role !== "admin") return;
    try {
      const res = await api.get<{ items: User[] }>("/api/users?limit=50");
      if (res.data?.items) setUsers(res.data.items);
    } catch {}
  };

  useEffect(() => {
    loadUsers();
  }, [user]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast("New passwords do not match", "error");
      return;
    }
    if (newPassword.length < 8) {
      toast("Password must be at least 8 characters", "error");
      return;
    }

    setChangingPass(true);
    try {
      await api.post("/api/auth/password/change", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast("Password changed! Please log in again.");
      logout();
    } catch (err: any) {
      toast(err?.message || "Failed to change password", "error");
    } finally {
      setChangingPass(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername || !newEmail || !newUserPass) {
      toast("All fields are required", "error");
      return;
    }
    setSubmittingUser(true);
    try {
      await api.post("/api/users", {
        username: newUsername,
        email: newEmail,
        password: newUserPass,
        role: newUserRole,
      });
      toast("User provisioned successfully!");
      setCreateUserModalOpen(false);
      setNewUsername("");
      setNewEmail("");
      setNewUserPass("");
      loadUsers();
    } catch (err: any) {
      toast(err?.message || "Failed to create user", "error");
    } finally {
      setSubmittingUser(false);
    }
  };

  const handleToggleStatus = async (targetUser: User) => {
    const nextStatus = targetUser.status === "active" ? "suspended" : "active";
    try {
      await api.patch(`/api/users/${targetUser.id}/status`, { status: nextStatus });
      toast(`User status set to ${nextStatus}`);
      loadUsers();
    } catch (err: any) {
      toast(err?.message || "Failed to update status", "error");
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            <ShinyText>Security & System Administration</ShinyText>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Authentication settings, credential rotation, and user role provisioning.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Password Change Form */}
          <SpotlightCard className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <KeyRound className="w-4 h-4 text-indigo-500" />
              <h3 className="text-sm font-bold text-white">Change Master Password</h3>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-3">
              <Input
                label="Current Password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <Input
                label="New Password"
                type="password"
                placeholder="Min 8 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
              <Input
                label="Confirm New Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />

              <div className="pt-2">
                <ShinyButton type="submit" loading={changingPass} className="w-full text-xs py-2.5">
                  Update Password
                </ShinyButton>
              </div>
            </form>
          </SpotlightCard>

          {/* Session Info */}
          <SpotlightCard className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-4 h-4 text-emerald-500" />
              <h3 className="text-sm font-bold text-white">Active Session Security</h3>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400">Authenticated Username:</span>
                <span className="font-bold text-white">{user?.username}</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400">Primary Role:</span>
                <Badge variant={user?.role === "admin" ? "purple" : "info"}>
                  {user?.role?.toUpperCase()}
                </Badge>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400">Cookie Security:</span>
                <span className="text-emerald-400 font-semibold">SameSite / HttpOnly</span>
              </div>
              <div className="flex justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400">Hash Algorithm:</span>
                <span className="font-mono text-indigo-400">Argon2id</span>
              </div>
            </div>
          </SpotlightCard>
        </div>

        {/* Admin User Management Table */}
        {user?.role === "admin" && (
          <SpotlightCard className="p-6">
            <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">System Users & Roles</h3>
                <p className="text-xs text-slate-400">
                  Provision new administrators, collectors, or read-only viewers
                </p>
              </div>

              <ShinyButton
                onClick={() => setCreateUserModalOpen(true)}
                className="text-xs py-2 px-3 rounded-xl"
              >
                <UserPlus className="w-3.5 h-3.5 mr-1" />
                Provision User
              </ShinyButton>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3">Username</th>
                    <th className="p-3">Email</th>
                    <th className="p-3">Role</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Created</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td className="p-3 font-semibold text-white">{u.username}</td>
                      <td className="p-3 text-slate-400">{u.email}</td>
                      <td className="p-3">
                        <Badge variant={u.role === "admin" ? "purple" : u.role === "collector" ? "info" : "neutral"}>
                          {u.role}
                        </Badge>
                      </td>
                      <td className="p-3">
                        <StatusBadge status={u.status} />
                      </td>
                      <td className="p-3 text-slate-400">{formatDateTime(u.created_at)}</td>
                      <td className="p-3 text-right">
                        {u.id !== user.id && (
                          <Button
                            variant={u.status === "active" ? "danger" : "success"}
                            size="sm"
                            onClick={() => handleToggleStatus(u)}
                            className="text-xs py-1 px-2"
                          >
                            {u.status === "active" ? "Suspend" : "Activate"}
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SpotlightCard>
        )}

        {/* Provision User Modal */}
        <Modal
          isOpen={createUserModalOpen}
          onClose={() => setCreateUserModalOpen(false)}
          title="Provision New Account"
          description="Create credentials for administrative or collection staff"
          maxWidth="md"
        >
          <form onSubmit={handleCreateUser} className="space-y-4">
            <Input
              label="Username"
              placeholder="e.g. collector3"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              required
            />
            <Input
              label="Email"
              type="email"
              placeholder="staff@giftledger.dev"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              required
            />
            <Input
              label="Initial Temporary Password"
              type="password"
              placeholder="Min 8 characters"
              value={newUserPass}
              onChange={(e) => setNewUserPass(e.target.value)}
              required
            />
            <Select
              label="Assigned System Role"
              value={newUserRole}
              onChange={(e) => setNewUserRole(e.target.value as UserRole)}
            >
              <option value="collector">Collector (Shift & Cash Collections)</option>
              <option value="viewer">Viewer (Read-Only Reports)</option>
              <option value="admin">Administrator (Full Access)</option>
            </Select>

            <div className="pt-3 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setCreateUserModalOpen(false)}>
                Cancel
              </Button>
              <ShinyButton type="submit" loading={submittingUser}>
                Create Account
              </ShinyButton>
            </div>
          </form>
        </Modal>
      </div>
    </AppShell>
  );
}
