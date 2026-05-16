"use client";

import { Sparkles, TrendingUp, Wallet } from "lucide-react";
import type { DashboardStats } from "@/types";
import { formatFcfa } from "@/components/kpi-card";

export function DashboardSidebarWidgets({ stats }: { stats: DashboardStats }) {
  const availablePct = Math.min(
    100,
    stats.total_wallet_balance > 0
      ? Math.round(
          (stats.total_wallet_balance /
            (stats.total_wallet_balance + stats.total_locked_balance + 1)) *
            100,
        )
      : 0,
  );

  return (
    <div className="space-y-4">
      <div className="dashboard-card p-5">
        <p className="text-sm font-semibold text-muted-foreground mb-4">Financier</p>
        <div className="rounded-xl bg-accent/60 p-4 mb-5">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">Insight NoviKash</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {stats.pending_kyc > 0
              ? `${stats.pending_kyc} dossier(s) KYC en attente de validation.`
              : "Plateforme stable — aucun dossier KYC urgent."}
          </p>
        </div>

        <p className="text-center text-sm font-medium text-muted-foreground mb-3">
          Solde plateforme
        </p>
        <div className="relative mx-auto h-36 w-36">
          <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke="#f5f3ef"
              strokeWidth="10"
            />
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke="#ff5722"
              strokeWidth="10"
              strokeDasharray={`${availablePct * 2.64} 264`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-lg font-bold">{availablePct}%</span>
            <span className="text-[10px] text-muted-foreground">disponible</span>
          </div>
        </div>
        <p className="text-center text-sm font-bold mt-3">
          {formatFcfa(stats.total_wallet_balance)}
        </p>

        <div className="mt-5 grid grid-cols-2 gap-3 border-t border-border pt-4">
          <div>
            <p className="text-xs text-muted-foreground">Prêts actifs</p>
            <p className="font-bold flex items-center gap-1">
              {stats.active_loans}
              <TrendingUp className="h-3 w-3 text-primary" />
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">En attente</p>
            <p className="font-bold">{stats.pending_loans}</p>
          </div>
        </div>
      </div>

      <div className="dashboard-card overflow-hidden p-0">
        <div className="p-5 pb-3">
          <p className="text-sm font-medium text-muted-foreground">Wallet principal</p>
          <p className="text-xs text-muted-foreground">Vue agrégée utilisateurs</p>
        </div>
        <div className="mx-5 mb-5 rounded-2xl bg-gradient-to-br from-zinc-900 to-zinc-800 p-5 text-white shadow-lg">
          <div className="flex justify-between items-start mb-8">
            <Wallet className="h-5 w-5 opacity-80" />
            <span className="text-xs font-medium opacity-70">NOVIKASH</span>
          </div>
          <p className="text-xs opacity-60 tracking-widest mb-1">•••• •••• •••• 4289</p>
          <div className="flex justify-between items-end mt-4">
            <span className="text-[10px] opacity-50">Solde total</span>
            <span className="text-lg font-bold">
              {formatFcfa(stats.total_wallet_balance + stats.total_locked_balance)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
