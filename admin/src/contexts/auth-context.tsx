"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { apiClient, clearToken, getToken, setToken, ApiError } from "@/lib/api";
import type { StaffMe } from "@/types";

interface AuthContextValue {
  staff: StaffMe | null;
  loading: boolean;
  login: (phone: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STAFF_ROLES = new Set(["SUPERADMIN", "ADMIN", "SUPPORT", "AUDITOR"]);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [staff, setStaff] = useState<StaffMe | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setStaff(null);
      setLoading(false);
      return;
    }
    try {
      const me = await apiClient.me();
      if (!STAFF_ROLES.has(me.role)) {
        clearToken();
        setStaff(null);
      } else {
        setStaff(me);
      }
    } catch {
      clearToken();
      setStaff(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (phone: string, password: string) => {
    const res = await apiClient.login(phone, password);
    if (!STAFF_ROLES.has(res.role)) {
      throw new ApiError(403, "Accès réservé au personnel NoviKash");
    }
    setToken(res.access_token);
    await refresh();
    router.push("/");
  };

  const logout = () => {
    clearToken();
    setStaff(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ staff, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
