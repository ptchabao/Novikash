"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Plus, Minus } from "lucide-react";
import { apiClient } from "@/lib/api";
import type { AdminUser } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatFcfa } from "@/components/kpi-card";
import { WalletAdjustDialog } from "@/components/wallet-adjust-dialog";
import { useAuth } from "@/contexts/auth-context";
import { can } from "@/lib/permissions";

export default function UserDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const { staff } = useAuth();
  const [user, setUser] = useState<AdminUser | null>(null);
  const [dialog, setDialog] = useState<"credit" | "debit" | null>(null);

  const load = () => apiClient.user(id).then(setUser).catch(console.error);

  useEffect(() => {
    load();
  }, [id]);

  if (!user) return <p>Chargement...</p>;

  return (
    <div className="space-y-6">
      <Link href="/users" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Retour
      </Link>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">{user.phone}</h1>
          <div className="mt-2 flex gap-2">
            <Badge>{user.role}</Badge>
            {user.is_kyc_verified && <Badge className="bg-green-600">KYC OK</Badge>}
          </div>
        </div>
        <div className="flex gap-2">
          {can(staff, "wallets.credit") && (
            <Button className="bg-green-600 hover:bg-green-700 gap-2" onClick={() => setDialog("credit")}>
              <Plus className="h-4 w-4" /> Créditer
            </Button>
          )}
          {can(staff, "wallets.debit") && (
            <Button variant="destructive" className="gap-2" onClick={() => setDialog("debit")}>
              <Minus className="h-4 w-4" /> Débiter
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="dashboard-card p-6">
          <p className="text-sm font-medium text-muted-foreground mb-2">Portefeuille</p>
          <p className="text-3xl font-bold">{user.wallet ? formatFcfa(user.wallet.balance_available) : "—"}</p>
          <p className="text-sm text-muted-foreground mt-2">
            Bloqué : {user.wallet ? formatFcfa(user.wallet.balance_locked) : "—"}
          </p>
        </div>
        <div className="dashboard-card p-6">
          <p className="text-sm font-medium text-muted-foreground mb-3">Identité</p>
          <div className="space-y-1 text-sm">
            <p>Type : {user.identity_type || "—"}</p>
            <p>N° : {user.identity_number || "—"}</p>
            {user.identity_document_url && (
              <a href={user.identity_document_url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                Voir le document
              </a>
            )}
          </div>
        </div>
      </div>

      {dialog && (
        <WalletAdjustDialog
          open={!!dialog}
          onOpenChange={() => setDialog(null)}
          userId={user.id}
          userPhone={user.phone}
          mode={dialog}
          onSuccess={load}
        />
      )}
    </div>
  );
}
