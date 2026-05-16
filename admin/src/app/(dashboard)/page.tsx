"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  Wallet,
  Landmark,
  ShieldCheck,
  ArrowDownToLine,
  ArrowUpFromLine,
  CreditCard,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import type { DashboardStats, Transaction } from "@/types";
import { KpiCard, formatFcfa } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { DashboardCashflowChart } from "@/components/dashboard-cashflow-chart";
import { DashboardSidebarWidgets } from "@/components/dashboard-sidebar-widgets";
import { DataTableShell } from "@/components/data-table-shell";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const TX_ICONS: Record<string, string> = {
  DEPOSIT: "💰",
  WITHDRAW: "📤",
  TRANSFER: "↔️",
  ADMIN_CREDIT: "✅",
  ADMIN_DEBIT: "➖",
  LOAN_DISBURSEMENT: "⚡",
  LOAN_REPAYMENT: "🔄",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentTx, setRecentTx] = useState<Transaction[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    apiClient.dashboard().then(setStats).catch(console.error);
    apiClient.transactions().then((txs) => setRecentTx(txs.slice(0, 8))).catch(console.error);
  }, []);

  const filtered = recentTx.filter(
    (t) =>
      !search ||
      t.reference.toLowerCase().includes(search.toLowerCase()) ||
      t.type.toLowerCase().includes(search.toLowerCase()) ||
      String(t.amount).includes(search),
  );

  if (!stats) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader showExport showPeriod />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          title="Volume wallets"
          value={formatFcfa(stats.total_wallet_balance)}
          growth={`${stats.verified_users} comptes`}
          growthLabel="utilisateurs vérifiés"
        />
        <KpiCard
          title="Prêts actifs"
          value={stats.active_loans}
          growth={`+${stats.pending_loans} en file`}
          growthLabel="demandes en attente"
        />
        <KpiCard
          title="Dépôts du jour"
          value={formatFcfa(stats.deposits_today)}
          growthLabel={`${stats.transactions_today} opérations`}
        />
        <KpiCard
          title="Retraits du jour"
          value={formatFcfa(stats.withdrawals_today)}
          growth={stats.manual_credits_today > 0 ? formatFcfa(stats.manual_credits_today) : undefined}
          growthLabel={stats.manual_credits_today > 0 ? "crédits manuels" : "flux sortants"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <DashboardCashflowChart stats={stats} />

          <DataTableShell
            title="Transactions récentes"
            searchPlaceholder="Rechercher par référence, type ou montant..."
            searchValue={search}
            onSearchChange={setSearch}
          >
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-border">
                  <TableHead className="text-muted-foreground font-medium">Transaction</TableHead>
                  <TableHead className="text-muted-foreground font-medium">Type</TableHead>
                  <TableHead className="text-muted-foreground font-medium">Date</TableHead>
                  <TableHead className="text-muted-foreground font-medium text-right">Montant</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((t) => (
                  <TableRow key={t.id} className="border-border">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-sm">
                          {TX_ICONS[t.type] || "📋"}
                        </span>
                        <div>
                          <p className="font-medium text-sm">{t.type.replace(/_/g, " ")}</p>
                          <p className="text-xs text-muted-foreground font-mono">
                            {t.reference.slice(0, 14)}…
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="rounded-full font-normal">
                        {t.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(t.created_at).toLocaleDateString("fr-FR", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </TableCell>
                    <TableCell
                      className={`text-right font-semibold ${
                        ["DEPOSIT", "ADMIN_CREDIT", "LOAN_DISBURSEMENT"].includes(t.type)
                          ? "text-foreground"
                          : "text-muted-foreground"
                      }`}
                    >
                      {["WITHDRAW", "ADMIN_DEBIT", "LOAN_REPAYMENT"].includes(t.type) ? "−" : "+"}
                      {formatFcfa(t.amount)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">⋯</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="border-t border-border p-4 text-center">
              <Link href="/transactions" className="text-sm font-medium text-primary hover:underline">
                Voir toutes les transactions →
              </Link>
            </div>
          </DataTableShell>
        </div>

        <div className="space-y-4">
          <DashboardSidebarWidgets stats={stats} />

          <div className="dashboard-card p-5">
            <p className="text-sm font-semibold mb-4">Accès rapide</p>
            <div className="grid gap-2">
              {[
                { href: "/users", label: "Utilisateurs", icon: Users },
                { href: "/loans", label: "Prêts", icon: Landmark },
                { href: "/kyc", label: "KYC", icon: ShieldCheck },
                { href: "/novi-plus", label: "NOVI+", icon: CreditCard },
              ].map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 rounded-xl border border-border px-4 py-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                >
                  <Icon className="h-4 w-4 text-primary" />
                  {label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
