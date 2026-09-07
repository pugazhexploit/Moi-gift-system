"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/hooks/useAuth";
import { SpotlightCard } from "@/components/ui/SpotlightCard";
import { ShinyButton } from "@/components/ui/ShinyButton";
import { ShinyText } from "@/components/ui/ShinyText";
import { Input } from "@/components/ui/Input";
import {
  Shield,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Zap,
  Sparkles,
  ArrowRight,
  Activity,
  Users,
  Gift,
  BarChart3,
  Lock,
  Menu,
  X,
  Crown,
  Eye,
  EyeOff,
  Smartphone,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface HealthStatus {
  status: "ok" | "degraded" | "checking" | "error";
  mongodb?: string;
  label?: string;
}

export default function LandingPage() {
  const { user, login } = useAuth();
  const router = useRouter();
  const loginRef = useRef<HTMLDivElement>(null);
  const identifierInputRef = useRef<HTMLInputElement>(null);
  const passwordInputRef = useRef<HTMLInputElement>(null);
  const identifierRef = identifierInputRef;
  const passwordRef = passwordInputRef;

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appliedRole, setAppliedRole] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus>({ status: "checking" });
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    // Ensure form starts 100% clean and empty on initial page load and refresh
    setIdentifier("");
    setPassword("");
    setAppliedRole("");
    setSuccessMessage(null);
    if (identifierInputRef.current) identifierInputRef.current.value = "";
    if (passwordInputRef.current) passwordInputRef.current.value = "";
  }, []);

  useEffect(() => {
    if (user) {
      router.replace(user.role === "collector" ? "/collectors/mobile" : "/dashboard");
    }
  }, [user, router]);

  useEffect(() => {
    const check = async () => {
      try {
        const response = await fetch("/api/health");
        const json = await response.json().catch(() => null);
        const data = json?.data;
        if (data?.mongodb === "available" || data?.status === "healthy") {
          setHealth({
            status: "ok",
            mongodb: "available",
            label: "Backend API healthy · MongoDB Connected",
          });
        } else if (response.ok || response.status === 503 || data?.status === "degraded") {
          setHealth({
            status: "degraded",
            mongodb: data?.mongodb || "unavailable",
            label: "Backend API online · MongoDB disconnected (Add IP to Atlas whitelist)",
          });
        } else {
          setHealth({
            status: "error",
            mongodb: "unavailable",
            label: "Backend offline — check connection",
          });
        }
      } catch {
        setHealth({
          status: "error",
          mongodb: "unavailable",
          label: "Backend server offline — check port 8000",
        });
      }
    };
    check();
    const interval = setInterval(check, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);
    const cleanId = (identifier || identifierRef.current?.value || "").trim();
    const cleanPw = (password || passwordRef.current?.value || "").trim();
    if (!cleanId || !cleanPw) { setError("Please fill in both identifier and password."); return; }
    setLoading(true);
    try { await login(cleanId, cleanPw); }
    catch (err: any) { setError(err?.message || "Invalid credentials or account locked."); }
    finally { setLoading(false); }
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
      login(u, p).catch((err: any) => { setError(err?.message || "Login failed."); setLoading(false); });
    }
  };

  const scrollToLogin = () => loginRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });

  const healthColor =
    health.status === "ok"
      ? "text-emerald-400"
      : health.status === "degraded"
      ? "text-amber-400"
      : health.status === "checking"
      ? "text-indigo-400"
      : "text-rose-400";

  const healthDot =
    health.status === "ok"
      ? "bg-emerald-400"
      : health.status === "degraded"
      ? "bg-amber-400"
      : health.status === "checking"
      ? "bg-indigo-400 animate-pulse"
      : "bg-rose-400";

  const healthLabel =
    health.label ||
    (health.status === "checking"
      ? "Connecting to backend…"
      : health.status === "ok"
      ? "Backend API healthy"
      : health.status === "degraded"
      ? "Backend API online · MongoDB disconnected"
      : "Backend offline — check connection");

  const ROLES = [
    { label: "👑 Admin",      role: "Admin",       u: "admin@giftledger.dev",     p: "Admin@GiftLedger123!", active: "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30",   inactive: "bg-indigo-950/60 border-indigo-800/60 text-indigo-300 hover:bg-indigo-900/80"   },
    { label: "📱 Collector",  role: "Collector 1", u: "collector1@giftledger.dev", p: "Collector1@123!",      active: "bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/30", inactive: "bg-emerald-950/60 border-emerald-800/60 text-emerald-300 hover:bg-emerald-900/80" },
    { label: "👁 Viewer",     role: "Viewer",      u: "viewer@giftledger.dev",     p: "Viewer@123!",          active: "bg-slate-700 text-white border-slate-600 shadow-md",                           inactive: "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700/80"              },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 relative overflow-x-hidden">
      {/* Ambient glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-96 h-96 bg-violet-600/8 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#1e293b18_1px,transparent_1px),linear-gradient(to_bottom,#1e293b18_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      {/* ── NAVBAR ── */}
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-base bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">GiftLedger</span>
          </div>

          <nav className="hidden md:flex items-center gap-2">
            <button onClick={() => { handleQuickFill("admin@giftledger.dev", "Admin@GiftLedger123!", "Admin", true); scrollToLogin(); }} className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border border-indigo-500/40 bg-indigo-950/60 text-indigo-300 hover:bg-indigo-900/70 transition-all">
              <Crown className="w-3.5 h-3.5" /> Admin
            </button>
            <button onClick={() => { handleQuickFill("collector1@giftledger.dev", "Collector1@123!", "Collector 1", true); scrollToLogin(); }} className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border border-emerald-500/40 bg-emerald-950/60 text-emerald-300 hover:bg-emerald-900/70 transition-all">
              <Smartphone className="w-3.5 h-3.5" /> Collector
            </button>
            <button onClick={() => { handleQuickFill("viewer@giftledger.dev", "Viewer@123!", "Viewer", true); scrollToLogin(); }} className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border border-slate-600/60 bg-slate-800/60 text-slate-300 hover:bg-slate-700/70 transition-all">
              <Eye className="w-3.5 h-3.5" /> Viewer
            </button>
            <div className="w-px h-5 bg-slate-700 mx-1" />
            <ShinyButton onClick={scrollToLogin} className="px-4 py-2 text-xs rounded-xl">
              Get Started <ArrowRight className="w-3.5 h-3.5" />
            </ShinyButton>
          </nav>

          <button className="md:hidden p-2 rounded-xl text-slate-400 hover:bg-slate-800" onClick={() => setNavOpen(!navOpen)}>
            {navOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {navOpen && (
          <div className="md:hidden border-t border-slate-800 bg-slate-950/95 backdrop-blur-2xl p-4 space-y-2">
            {ROLES.map(({ label, u, p, role }) => (
              <button key={role} onClick={() => { handleQuickFill(u, p, role, true); setNavOpen(false); scrollToLogin(); }} className="w-full text-left px-4 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors">
                {label}
              </button>
            ))}
            <button onClick={() => { setNavOpen(false); scrollToLogin(); }} className="w-full px-4 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors">
              Get Started →
            </button>
          </div>
        )}
      </header>

      {/* ── HERO ── */}
      <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-950/50 text-indigo-300 text-xs font-semibold mb-6 shadow-lg shadow-indigo-950/40">
          <div className={`w-1.5 h-1.5 rounded-full ${healthDot}`} />
          <Activity className="w-3 h-3" />
          <span className={healthColor}>{healthLabel}</span>
        </div>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-none">
          <ShinyText className="text-5xl sm:text-6xl lg:text-7xl font-extrabold">GiftLedger</ShinyText>
          <br />
          <span className="text-2xl sm:text-3xl lg:text-4xl font-semibold text-slate-400 mt-2 block">
            Guest Gift &amp; Money Monitoring
          </span>
        </h1>

        <p className="max-w-2xl mx-auto text-slate-400 text-base sm:text-lg leading-relaxed mb-8">
          Tamper-evident financial accounting, physical gift cataloguing, cash drawer reconciliation,
          and executive analytics — purpose-built for weddings, receptions, and community events.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-16">
          <ShinyButton onClick={scrollToLogin} className="px-8 py-3.5 text-sm rounded-2xl font-semibold shadow-xl shadow-indigo-600/25">
            Get Started <ArrowRight className="w-4 h-4" />
          </ShinyButton>
          <button onClick={() => handleQuickFill("admin@giftledger.dev", "Admin@GiftLedger123!", "Admin", true)} className="flex items-center gap-2 px-6 py-3.5 rounded-2xl border border-slate-700 text-slate-300 text-sm font-medium hover:bg-slate-800/60 hover:border-slate-600 transition-all">
            <Zap className="w-4 h-4 text-indigo-400" /> Instant Demo Login
          </button>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3 text-xs text-slate-500">
          {[
            { icon: Shield,    label: "Argon2id Encryption" },
            { icon: Lock,      label: "HTTP-only Cookies"   },
            { icon: Users,     label: "Role-Based Access"   },
            { icon: Gift,      label: "Gift Registry"       },
            { icon: BarChart3, label: "Fintech Analytics"   },
            { icon: Activity,  label: "Audit Trail"         },
          ].map(({ icon: Icon, label }) => (
            <span key={label} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-slate-800 bg-slate-900/60">
              <Icon className="w-3 h-3 text-indigo-400" />{label}
            </span>
          ))}
        </div>
      </section>

      {/* ── LOGIN CARD ── */}
      <section ref={loginRef} className="relative z-10 max-w-md mx-auto px-4 sm:px-6 pb-24">
        <SpotlightCard className="p-8 border-slate-800 bg-slate-900/90 shadow-2xl backdrop-blur-xl">
          <div className="text-center mb-6">
            <div className="relative inline-block mb-3">
              <button type="button" onClick={() => handleQuickFill("admin@giftledger.dev", "Admin@GiftLedger123!", "Admin")} title="Click to auto-apply Admin credentials" className="relative inline-flex p-4 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border-2 border-indigo-500/50 text-indigo-400 shadow-xl shadow-indigo-500/20 hover:scale-105 active:scale-95 transition-all cursor-pointer group focus:outline-none focus:ring-4 focus:ring-indigo-500/30">
                <ShieldCheck className="w-8 h-8 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
                <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-4 w-4 bg-indigo-500 text-[9px] font-bold text-white items-center justify-center">★</span>
                </span>
              </button>
            </div>
            <p className="text-xs font-semibold text-indigo-400 mb-1 flex items-center justify-center gap-1.5">
              <Zap className="w-3.5 h-3.5 fill-indigo-400" /> Tap Shield icon to Auto-Fill Admin
            </p>
            <h2 className="text-xl font-bold tracking-tight mb-0.5">Sign In to GiftLedger</h2>
            <p className="text-xs text-slate-400">Guest Gift &amp; Money Collection System</p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" /><span>{error}</span>
            </div>
          )}
          {successMessage && !error && (
            <div className="mb-4 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" /><span>{successMessage}</span>
              </div>
              <button type="button" onClick={() => { setIdentifier(""); setPassword(""); setSuccessMessage(null); }} className="text-[10px] text-slate-400 hover:text-slate-200 underline">Clear</button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off" noValidate>
            {/* Browser autofill decoy trap: absorbs browser password manager autofill on localhost */}
            <div className="sr-only" aria-hidden="true" style={{ position: "absolute", opacity: 0, height: 0, width: 0, overflow: "hidden", zIndex: -1 }}>
              <input type="text" name="chrome_decoy_user" tabIndex={-1} autoComplete="off" defaultValue="" />
              <input type="password" name="chrome_decoy_pass" tabIndex={-1} autoComplete="off" defaultValue="" />
            </div>

            <Input
              ref={identifierInputRef}
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
            <Input
              ref={passwordInputRef}
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
            <div className="space-y-2 pt-2">
              <ShinyButton type="submit" loading={loading} className="w-full justify-center py-3 text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/20">
                Sign In to Ledger
              </ShinyButton>
              <button type="button" disabled={loading} onClick={() => handleQuickFill("admin@giftledger.dev", "Admin@GiftLedger123!", "Admin", true)} className="w-full py-2.5 px-3 rounded-xl border border-indigo-500/40 bg-indigo-950/40 hover:bg-indigo-900/50 text-indigo-300 text-xs font-medium flex items-center justify-center gap-2 transition-all active:scale-95 cursor-pointer disabled:opacity-50">
                <Zap className="w-3.5 h-3.5 fill-indigo-400" /> Instant 1-Click Login as Admin
              </button>
            </div>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-800/80">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 text-center">Auto-Fill Demo Roles</p>
            <div className="grid grid-cols-3 gap-2">
              {ROLES.map(({ label, role, u, p, active, inactive }) => (
                <button key={role} type="button" onClick={() => handleQuickFill(u, p, role)} className={`text-xs py-2 px-2 rounded-xl border font-semibold transition-all ${appliedRole === role ? active : inactive}`}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
            <Shield className="w-3.5 h-3.5 text-indigo-400" />
            <span>Encrypted with Argon2id + SameSite Cookies</span>
          </div>
        </SpotlightCard>

        {/* API Health indicator */}
        <div className="mt-4 flex items-center gap-3 text-xs text-slate-500 bg-slate-900/60 border border-slate-800/80 rounded-2xl px-5 py-3">
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${healthDot}`} />
          <span className={`font-medium ${healthColor}`}>
            {health.status === "checking" && "Checking API health…"}
            {health.status === "ok" && `Backend healthy · MongoDB connected`}
            {health.status === "degraded" && `Backend API online · MongoDB disconnected (Add IP to Atlas whitelist)`}
            {health.status === "error" && "Backend unreachable — start server at port 8000"}
          </span>
          <span className="ml-auto text-slate-600 font-mono">:8000/api/health</span>
        </div>
      </section>
    </div>
  );
}

