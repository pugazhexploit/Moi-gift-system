"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/hooks/useAuth";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyButton } from "@/components/ui/ShinyButton";
import { ShinyText } from "@/components/ui/ShinyText";
import { Input } from "@/components/ui/Input";
import { Shield, ShieldCheck, Lock, User, KeyRound, AlertCircle, CheckCircle2, Zap, Sparkles, Eye, EyeOff } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const { user, login } = useAuth();
  const router = useRouter();
  const identifierInputRef = useRef<HTMLInputElement>(null);
  const passwordInputRef = useRef<HTMLInputElement>(null);
  const identifierRef = identifierInputRef;
  const passwordRef = passwordInputRef;

  // Clean initial state — no credentials pre-filled on page load
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appliedRole, setAppliedRole] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Ensure form starts 100% clean and empty on initial page load and refresh
  useEffect(() => {
    setIdentifier("");
    setPassword("");
    setAppliedRole("");
    setSuccessMessage(null);
    if (identifierInputRef.current) identifierInputRef.current.value = "";
    if (passwordInputRef.current) passwordInputRef.current.value = "";
  }, []);

  // If already logged in, redirect immediately
  useEffect(() => {
    if (user) {
      const target = user.role === "collector" ? "/collectors/mobile" : "/dashboard";
      router.push(target);
    }
  }, [user, router]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    const cleanIdentifier = (identifier || identifierRef.current?.value || "").trim();
    const cleanPassword = (password || passwordRef.current?.value || "").trim();

    if (!cleanIdentifier || !cleanPassword) {
      setError("Please fill in both identifier and password");
      return;
    }

    setLoading(true);
    try {
      await login(cleanIdentifier, cleanPassword);
    } catch (err: any) {
      setError(err?.message || "Invalid credentials or account locked");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = (u: string, p: string, roleName: string, autoSubmit = false) => {
    setIdentifier(u);
    setPassword(p);
    if (identifierRef.current) identifierRef.current.value = u;
    if (passwordRef.current) passwordRef.current.value = p;
    setError(null);
    setAppliedRole(roleName);
    setSuccessMessage(`✓ ${roleName} credentials applied!`);

    if (autoSubmit) {
      setLoading(true);
      login(u, p).catch((err: any) => {
        setError(err?.message || "Login failed");
        setLoading(false);
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 text-slate-100 relative overflow-hidden">
      {/* Ambient background glow inspired by React Bits */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        <SpotlightCard className="p-8 border-slate-800 bg-slate-900/90 shadow-2xl backdrop-blur-xl">
          {/* Header */}
          <div className="text-center mb-6">
            {/* Clickable Admin Shield Icon with visual ring and auto-apply handler */}
            <div className="relative inline-block mb-3">
              <button
                type="button"
                onClick={() => handleQuickFill("admin@giftledger.dev", "Admin@GiftLedger123!", "Admin")}
                title="Click icon to auto-apply Admin credentials"
                className="relative inline-flex p-4 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border-2 border-indigo-500/50 text-indigo-400 shadow-xl shadow-indigo-500/20 hover:scale-105 active:scale-95 transition-all cursor-pointer group focus:outline-none focus:ring-4 focus:ring-indigo-500/30"
              >
                <ShieldCheck className="w-8 h-8 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
                <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-4 w-4 bg-indigo-500 text-[9px] font-bold text-white items-center justify-center">★</span>
                </span>
              </button>
            </div>

            <p className="text-xs font-semibold text-indigo-400 mb-1 flex items-center justify-center gap-1.5">
              <Zap className="w-3.5 h-3.5 fill-indigo-400" />
              <span>Tap Shield icon to Auto-Fill Admin</span>
            </p>

            <h1 className="text-2xl font-bold tracking-tight mb-1">
              <ShinyText>GiftLedger</ShinyText>
            </h1>
            <p className="text-xs text-slate-400 font-medium">
              Guest Gift & Money Collection Monitoring System
            </p>
          </div>

          {/* Feedback messages */}
          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-400 text-xs flex items-center gap-2 animate-in fade-in">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMessage && !error && (
            <div className="mb-4 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs flex items-center justify-between gap-2 animate-in fade-in">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-400" />
                <span>{successMessage}</span>
              </div>
              <button
                type="button"
                onClick={() => { setIdentifier(""); setPassword(""); setSuccessMessage(null); }}
                className="text-[10px] text-slate-400 hover:text-slate-200 underline"
              >
                Clear
              </button>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off" noValidate>
            {/* Browser autofill decoy trap: absorbs browser password manager autofill on localhost */}
            <div className="sr-only" aria-hidden="true" style={{ position: "absolute", opacity: 0, height: 0, width: 0, overflow: "hidden", zIndex: -1 }}>
              <input type="text" name="chrome_decoy_user" tabIndex={-1} autoComplete="off" defaultValue="" />
              <input type="password" name="chrome_decoy_pass" tabIndex={-1} autoComplete="off" defaultValue="" />
            </div>

            <div>
              <Input
                ref={identifierRef}
                label="Username or Email"
                type="text"
                name="gl_login_identifier"
                id="gl_login_identifier"
                placeholder="Enter username or email"
                value={identifier}
                onChange={(e) => {
                  setIdentifier(e.target.value);
                  setError(null);
                }}
                autoComplete="off"
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck="false"
                required
                className="bg-slate-950/60 border-slate-800 focus:border-indigo-500 text-slate-100"
              />
            </div>

            <div>
              <Input
                ref={passwordRef}
                label="Password"
                type={showPassword ? "text" : "password"}
                name="gl_login_secret"
                id="gl_login_secret"
                placeholder="Enter password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError(null);
                }}
                autoComplete="new-password"
                required
                rightElement={
                  <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-slate-400 hover:text-slate-200 focus:outline-none p-1 transition-colors"
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                }
                className="bg-slate-950/60 border-slate-800 focus:border-indigo-500 text-slate-100"
              />
            </div>

            <div className="space-y-2 pt-2">
              <ShinyButton
                type="submit"
                loading={loading}
                className="w-full justify-center py-3 text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/20"
              >
                Sign In to Ledger
              </ShinyButton>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickFill("admin@giftledger.dev", "Admin@GiftLedger123!", "Admin", true)}
                className="w-full py-2.5 px-3 rounded-xl border border-indigo-500/40 bg-indigo-950/40 hover:bg-indigo-900/50 text-indigo-300 text-xs font-medium flex items-center justify-center gap-2 transition-all active:scale-98 cursor-pointer"
              >
                <Zap className="w-3.5 h-3.5 fill-indigo-400" />
                <span>Instant 1-Click Login as Admin</span>
              </button>
            </div>
          </form>

          {/* Quick Fill role selector buttons */}
          <div className="mt-6 pt-5 border-t border-slate-800/80">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 text-center">
              Auto-Fill Other Demo Roles
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill("admin@giftledger.dev", "Admin@GiftLedger123!", "Admin")}
                className={`text-xs py-2 px-2 rounded-xl border font-semibold transition-all ${
                  appliedRole === "Admin"
                    ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30"
                    : "bg-indigo-950/60 border-indigo-800/60 text-indigo-300 hover:bg-indigo-900/80"
                }`}
              >
                👑 Admin
              </button>

              <button
                type="button"
                onClick={() => handleQuickFill("collector1@giftledger.dev", "Collector1@123!", "Collector 1")}
                className={`text-xs py-2 px-2 rounded-xl border font-semibold transition-all ${
                  appliedRole === "Collector 1"
                    ? "bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/30"
                    : "bg-emerald-950/60 border-emerald-800/60 text-emerald-300 hover:bg-emerald-900/80"
                }`}
              >
                📱 Collector
              </button>

              <button
                type="button"
                onClick={() => handleQuickFill("viewer@giftledger.dev", "Viewer@123!", "Viewer")}
                className={`text-xs py-2 px-2 rounded-xl border font-semibold transition-all ${
                  appliedRole === "Viewer"
                    ? "bg-slate-700 text-white border-slate-600 shadow-md"
                    : "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700/80"
                }`}
              >
                👁️ Viewer
              </button>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
            <Shield className="w-3.5 h-3.5 text-indigo-400" />
            <span>Encrypted with Argon2id + SameSite Cookies</span>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
