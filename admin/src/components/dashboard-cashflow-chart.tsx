"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DashboardStats } from "@/types";
import { formatFcfa } from "@/components/kpi-card";

/** Visualisation inspirée de la maquette : entrées (orange) / sorties (noir) */
export function DashboardCashflowChart({ stats }: { stats: DashboardStats }) {
  const days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];
  const inflowBase = stats.deposits_today / 7 || 50000;
  const outflowBase = stats.withdrawals_today / 7 || 30000;

  const data = days.map((day, i) => ({
    day,
    inflow: Math.round(inflowBase * (0.7 + (i % 3) * 0.15)),
    outflow: -Math.round(outflowBase * (0.6 + (i % 4) * 0.12)),
  }));

  const totalIn = stats.deposits_today + stats.manual_credits_today;

  return (
    <div className="dashboard-card p-6">
      <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-lg font-semibold">Flux de trésorerie</h3>
          <p className="text-2xl font-bold mt-1">{formatFcfa(totalIn)}</p>
          <p className="text-xs text-muted-foreground mt-1">
            <span className="text-primary font-medium">+ entrées</span> aujourd&apos;hui
          </p>
        </div>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-primary" />
            Entrées (dépôts, crédits)
          </span>
          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-foreground" />
            Sorties (retraits)
          </span>
        </div>
      </div>

      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barGap={4} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e4de" />
            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: "#737373" }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#737373" }}
              tickFormatter={(v) => `${Math.abs(v / 1000)}k`}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: "1px solid #e8e4de",
                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              }}
              formatter={(value, name) => [
                formatFcfa(Math.abs(Number(value ?? 0))),
                name === "inflow" ? "Entrées" : "Sorties",
              ]}
            />
            <Bar dataKey="inflow" fill="#ff5722" radius={[6, 6, 0, 0]} maxBarSize={28} />
            <Bar dataKey="outflow" fill="#171717" radius={[0, 0, 6, 6]} maxBarSize={28} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
