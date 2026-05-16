"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { AdminUser } from "@/types";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/page-header";
import { useAuth } from "@/contexts/auth-context";
import { can } from "@/lib/permissions";
import { toast } from "sonner";

export default function KycPage() {
  const { staff } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);

  const load = () => apiClient.pendingKyc().then(setUsers).catch(console.error);

  useEffect(() => {
    load();
  }, []);

  const verify = async (userId: number, approved: boolean) => {
    try {
      await apiClient.verifyKyc(userId, approved);
      toast.success(approved ? "KYC approuvé" : "KYC refusé");
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Vérification KYC" subtitle="Identités en attente de validation" />

      {users.length === 0 ? (
        <p className="text-muted-foreground">Aucun dossier KYC en attente.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {users.map((u) => (
            <div key={u.id} className="dashboard-card p-5">
              <p className="text-lg font-semibold mb-4">{u.phone}</p>
              <div className="space-y-3 text-sm">
                <p>Type : {u.identity_type || "—"}</p>
                <p>N° : {u.identity_number || "—"}</p>
                {u.identity_document_url && (
                  <a
                    href={`${process.env.NEXT_PUBLIC_API_URL || ""}${u.identity_document_url}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-orange-600 hover:underline block"
                  >
                    Voir le document
                  </a>
                )}
                {can(staff, "kyc.verify") && (
                  <div className="flex gap-2 pt-2">
                    <Button size="sm" className="bg-green-600" onClick={() => verify(u.id, true)}>
                      Approuver
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => verify(u.id, false)}>
                      Refuser
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
