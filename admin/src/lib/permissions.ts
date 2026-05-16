import type { StaffMe } from "@/types";

export function can(staff: StaffMe | null, permission: string): boolean {
  if (!staff) return false;
  return staff.permissions.includes(permission);
}

export const NAV_ITEMS = [
  { href: "/", label: "Tableau de bord", icon: "LayoutDashboard", permission: "dashboard.view" },
  { href: "/users", label: "Utilisateurs", icon: "Users", permission: "users.read" },
  { href: "/transactions", label: "Transactions", icon: "ArrowLeftRight", permission: "transactions.read" },
  { href: "/loans", label: "Prêts", icon: "Landmark", permission: "loans.read" },
  { href: "/novi-plus", label: "NOVI+", icon: "Zap", permission: "loans.novi_verify" },
  { href: "/kyc", label: "KYC", icon: "ShieldCheck", permission: "kyc.read" },
] as const;
