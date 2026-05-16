"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import type { AdminUser } from "@/types";
import { PageHeader } from "@/components/page-header";
import { DataTableShell } from "@/components/data-table-shell";
import { formatFcfa } from "@/components/kpi-card";
import { Badge } from "@/components/ui/badge";
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

export default function UsersPage() {
  const { staff } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const t = setTimeout(() => {
      apiClient.users({ search: search || undefined }).then(setUsers).catch(console.error);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  return (
    <div className="space-y-8">
      <PageHeader title="Utilisateurs" subtitle="Comptes, rôles et portefeuilles" showExport />

      <DataTableShell
        title="Liste des comptes"
        searchPlaceholder="Rechercher par téléphone..."
        searchValue={search}
        onSearchChange={setSearch}
      >
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Utilisateur</TableHead>
              <TableHead>Rôle</TableHead>
              <TableHead>Solde disponible</TableHead>
              <TableHead>KYC</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id} className="border-border">
                <TableCell>
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-sm font-semibold text-accent-foreground">
                      {u.phone.slice(-2)}
                    </span>
                    <span className="font-medium">{u.phone}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={u.role === "USER" ? "secondary" : "default"} className="rounded-full">
                    {u.role}
                  </Badge>
                </TableCell>
                <TableCell className="font-medium">
                  {u.wallet ? formatFcfa(u.wallet.balance_available) : "—"}
                </TableCell>
                <TableCell>
                  {u.is_kyc_verified ? (
                    <Badge className="rounded-full bg-green-600">Vérifié</Badge>
                  ) : (
                    <Badge variant="outline" className="rounded-full">En attente</Badge>
                  )}
                </TableCell>
                <TableCell>
                  {can(staff, "users.read") && (
                    <Link href={`/users/${u.id}`} className="text-sm font-medium text-primary hover:underline">
                      Gérer →
                    </Link>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DataTableShell>
    </div>
  );
}
