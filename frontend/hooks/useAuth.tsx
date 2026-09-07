"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { User } from "@/types/api";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Try to load cached user or refresh session
    const saved = localStorage.getItem("giftledger_user");
    if (saved) {
      try {
        setUser(JSON.parse(saved));
      } catch {}
    }

    api
      .post<{ user: User }>("/api/auth/refresh")
      .then((res) => {
        if (res.data?.user) {
          setUser(res.data.user);
          localStorage.setItem("giftledger_user", JSON.stringify(res.data.user));
        }
      })
      .catch(() => {
        // If refresh fails, clear user if not already cleared
        setUser(null);
        localStorage.removeItem("giftledger_user");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const login = async (identifier: string, password: string) => {
    setLoading(true);
    try {
      const res = await api.post<{ user: User }>("/api/auth/login", {
        identifier,
        password,
      });
      if (res.data?.user) {
        setUser(res.data.user);
        localStorage.setItem("giftledger_user", JSON.stringify(res.data.user));
        if (typeof window !== "undefined") {
          window.location.href = res.data.user.role === "collector" ? "/collectors/mobile" : "/dashboard";
        } else {
          router.push(res.data.user.role === "collector" ? "/collectors/mobile" : "/dashboard");
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post("/api/auth/logout");
    } catch {}
    setUser(null);
    localStorage.removeItem("giftledger_user");
    router.push("/");
  };

  const refresh = async () => {
    try {
      const res = await api.post<{ user: User }>("/api/auth/refresh");
      if (res.data?.user) {
        setUser(res.data.user);
        localStorage.setItem("giftledger_user", JSON.stringify(res.data.user));
      }
    } catch {
      setUser(null);
      localStorage.removeItem("giftledger_user");
      router.push("/");
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
