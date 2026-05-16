const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("novikash_admin_token");
}

export function setToken(token: string) {
  localStorage.setItem("novikash_admin_token", token);
}

export function clearToken() {
  localStorage.removeItem("novikash_admin_token");
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)) || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const apiClient = {
  login: (phone: string, password: string) =>
    api<{ access_token: string; token_type: string; role: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ phone, password }),
    }),

  me: () => api<import("@/types").StaffMe>("/admin/me"),

  dashboard: () => api<import("@/types").DashboardStats>("/admin/dashboard"),

  users: (params?: { search?: string; role?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.role) q.set("role", params.role);
    const qs = q.toString();
    return api<import("@/types").AdminUser[]>(`/admin/users${qs ? `?${qs}` : ""}`);
  },

  user: (id: number) => api<import("@/types").AdminUser>(`/admin/users/${id}`),

  creditWallet: (userId: number, amount: number, reason: string) =>
    api<{ message: string; new_balance: number; reference: string }>(
      `/admin/users/${userId}/wallet/credit`,
      { method: "POST", body: JSON.stringify({ amount, reason }) },
    ),

  debitWallet: (userId: number, amount: number, reason: string) =>
    api<{ message: string; new_balance: number; reference: string }>(
      `/admin/users/${userId}/wallet/debit`,
      { method: "POST", body: JSON.stringify({ amount, reason }) },
    ),

  transactions: (params?: { type?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.type) q.set("type", params.type);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return api<import("@/types").Transaction[]>(`/admin/transactions${qs ? `?${qs}` : ""}`);
  },

  loans: (params?: { status?: string; loan_type?: string }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.loan_type) q.set("loan_type", params.loan_type);
    const qs = q.toString();
    return api<import("@/types").Loan[]>(`/admin/loans${qs ? `?${qs}` : ""}`);
  },

  updateLoanStatus: (loanId: number, status: string) =>
    api(`/admin/loans/${loanId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  pendingKyc: () => api<import("@/types").AdminUser[]>("/admin/kyc/pending"),

  verifyKyc: (userId: number, verified: boolean) =>
    api<import("@/types").AdminUser>(`/admin/kyc/${userId}/verify`, {
      method: "PATCH",
      body: JSON.stringify({ is_kyc_verified: verified }),
    }),

  pendingNoviPlus: () => api<import("@/types").NoviPlusProfile[]>("/admin/loans/novi-plus/pending"),

  verifyNoviPlus: (
    profileId: number,
    approve: boolean,
    verifiedSalary?: number,
    rejectionReason?: string,
  ) =>
    api(`/admin/loans/novi-plus/${profileId}/verify`, {
      method: "PATCH",
      body: JSON.stringify({
        approve,
        verified_salary: verifiedSalary,
        rejection_reason: rejectionReason,
      }),
    }),

  audit: () => api<{ admin_phone: string; action: string; target?: string; created_at: string }[]>("/admin/audit"),
};
