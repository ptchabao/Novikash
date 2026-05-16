"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { Loan } from "@/types";
import { formatFcfa } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { DataTableShell } from "@/components/data-table-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { useAuth } from "@/contexts/auth-context";
import { can } from "@/lib/permissions";
import { toast } from "sonner";

export default function LoansPage() {
  const { staff } = useAuth();
  const [loans, setLoans] = useState<Loan[]>([]);
  const [status, setStatus] = useState("all");
  const [loanType, setLoanType] = useState("all");

  const load = () => {
    apiClient
      .loans({
        status: status === "all" ? undefined : status,
        loan_type: loanType === "all" ? undefined : loanType,
      })
      .then(setLoans)
      .catch(console.error);
  };

  useEffect(() => {
    load();
  }, [status, loanType]);

  const setLoanStatus = async (id: number, newStatus: string) => {
    try {
      await apiClient.updateLoanStatus(id, newStatus);
      toast.success("Statut mis à jour");
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Prêts" subtitle="NOVI+ et ALOBA — supervision et gestion" showExport />

      <DataTableShell
        title="Portefeuille de prêts"
        filters={
          <div className="flex gap-2">
            <Select value={status} onValueChange={(v) => setStatus(v ?? "all")}>
              <SelectTrigger className="w-36 rounded-xl">
                <SelectValue placeholder="Statut" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous</SelectItem>
                {["PENDING", "ACTIVE", "REPAID", "REJECTED", "DEFAULTED"].map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={loanType} onValueChange={(v) => setLoanType(v ?? "all")}>
              <SelectTrigger className="w-36 rounded-xl">
                <SelectValue placeholder="Produit" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous</SelectItem>
                <SelectItem value="NOVI+">NOVI+</SelectItem>
                <SelectItem value="ALOBA">ALOBA</SelectItem>
              </SelectContent>
            </Select>
          </div>
        }
      >
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>ID</TableHead>
              <TableHead>Emprunteur</TableHead>
              <TableHead>Produit</TableHead>
              <TableHead>Montant</TableHead>
              <TableHead>Total dû</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Échéance</TableHead>
              {can(staff, "loans.manage") && <TableHead>Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loans.map((l) => (
              <TableRow key={l.id} className="border-border">
                <TableCell>#{l.id}</TableCell>
                <TableCell>{l.borrower_phone}</TableCell>
                <TableCell><Badge className="rounded-full">{l.loan_type}</Badge></TableCell>
                <TableCell>{formatFcfa(l.amount)}</TableCell>
                <TableCell>{formatFcfa(l.total_amount)}</TableCell>
                <TableCell><Badge variant="outline" className="rounded-full">{l.status}</Badge></TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(l.due_date).toLocaleDateString("fr-FR")}
                </TableCell>
                {can(staff, "loans.manage") && (
                  <TableCell className="space-x-1">
                    {l.status === "PENDING" && (
                      <>
                        <Button size="sm" variant="outline" className="rounded-lg" onClick={() => setLoanStatus(l.id, "ACTIVE")}>Activer</Button>
                        <Button size="sm" variant="ghost" onClick={() => setLoanStatus(l.id, "REJECTED")}>Rejeter</Button>
                      </>
                    )}
                    {l.status === "ACTIVE" && (
                      <Button size="sm" variant="outline" className="rounded-lg" onClick={() => setLoanStatus(l.id, "DEFAULTED")}>Défaut</Button>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DataTableShell>
    </div>
  );
}
