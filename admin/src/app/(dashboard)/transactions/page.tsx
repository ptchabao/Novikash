"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { Transaction } from "@/types";
import { formatFcfa } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { DataTableShell } from "@/components/data-table-shell";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const TX_TYPES = ["DEPOSIT", "WITHDRAW", "TRANSFER", "ADMIN_CREDIT", "ADMIN_DEBIT", "LOAN_DISBURSEMENT", "LOAN_REPAYMENT"];

export default function TransactionsPage() {
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [type, setType] = useState("all");
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    apiClient
      .transactions({
        type: type === "all" ? undefined : type,
        status: status === "all" ? undefined : status,
      })
      .then(setTxs)
      .catch(console.error);
  }, [type, status]);

  const filtered = txs.filter(
    (t) =>
      !search ||
      t.reference.toLowerCase().includes(search.toLowerCase()) ||
      t.type.toLowerCase().includes(search.toLowerCase()) ||
      (t.sender_phone?.includes(search) ?? false) ||
      (t.receiver_phone?.includes(search) ?? false),
  );

  return (
    <div className="space-y-8">
      <PageHeader
        title="Transactions"
        subtitle="Dépôts, retraits, transferts et opérations administrateur"
        showExport
        showPeriod
      />

      <DataTableShell
        title="Historique des transactions"
        searchPlaceholder="Rechercher par référence, type ou téléphone..."
        searchValue={search}
        onSearchChange={setSearch}
        filters={
          <>
            <Select value={type} onValueChange={(v) => setType(v ?? "all")}>
              <SelectTrigger className="w-40 rounded-xl">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous types</SelectItem>
                {TX_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={(v) => setStatus(v ?? "all")}>
              <SelectTrigger className="w-32 rounded-xl">
                <SelectValue placeholder="Statut" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous</SelectItem>
                <SelectItem value="SUCCESS">SUCCESS</SelectItem>
                <SelectItem value="PENDING">PENDING</SelectItem>
                <SelectItem value="FAILED">FAILED</SelectItem>
              </SelectContent>
            </Select>
          </>
        }
      >
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Transaction</TableHead>
              <TableHead>Catégorie</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Parties</TableHead>
              <TableHead className="text-right">Montant</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((t) => (
              <TableRow key={t.id} className="border-border">
                <TableCell>
                  <p className="font-medium text-sm">{t.type.replace(/_/g, " ")}</p>
                  <p className="text-xs text-muted-foreground font-mono">{t.reference.slice(0, 16)}</p>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="rounded-full">{t.status}</Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(t.created_at).toLocaleString("fr-FR")}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground max-w-[180px] truncate">
                  {t.sender_phone || "—"} → {t.receiver_phone || "—"}
                </TableCell>
                <TableCell className="text-right font-semibold">{formatFcfa(t.amount)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DataTableShell>
    </div>
  );
}
