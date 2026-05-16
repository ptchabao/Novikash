"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { NoviPlusProfile } from "@/types";
import { formatFcfa } from "@/components/kpi-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/auth-context";
import { can } from "@/lib/permissions";
import { toast } from "sonner";

export default function NoviPlusPage() {
  const { staff } = useAuth();
  const [profiles, setProfiles] = useState<NoviPlusProfile[]>([]);
  const [salaries, setSalaries] = useState<Record<number, string>>({});

  const load = () => apiClient.pendingNoviPlus().then(setProfiles).catch(console.error);

  useEffect(() => {
    load();
  }, []);

  const verify = async (profile: NoviPlusProfile, approve: boolean) => {
    try {
      await apiClient.verifyNoviPlus(
        profile.id,
        approve,
        approve ? parseFloat(salaries[profile.id] || String(profile.declared_salary)) : undefined,
        approve ? undefined : "Validation bancaire refusée par l'administrateur",
      );
      toast.success(approve ? "NOVI+ activé" : "Profil refusé");
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader title="Validation NOVI+" subtitle="Profils en attente de validation bancaire" />

      {profiles.length === 0 ? (
        <p className="text-muted-foreground">Aucun profil en attente.</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {profiles.map((p) => (
            <div key={p.id} className="dashboard-card p-5">
              <div className="flex items-center justify-between mb-1">
                <p className="text-lg font-semibold">{p.first_name} {p.last_name}</p>
                <Badge variant="outline" className="rounded-full">{p.status}</Badge>
              </div>
              <p className="text-sm text-muted-foreground mb-4">{p.user_phone}</p>
              <div className="space-y-2 text-sm">
                <p>Employeur : {p.employer}</p>
                <p>Contrat : {p.contract_type}</p>
                <p>Banque : {p.partner_bank}</p>
                <p>Compte : {p.account_number}</p>
                <p>Salaire déclaré : {formatFcfa(p.declared_salary)}</p>
                {can(staff, "loans.novi_verify") && (
                  <div className="pt-4 space-y-3">
                    <div>
                      <label className="text-xs text-muted-foreground">Salaire confirmé (FCFA)</label>
                      <Input
                        type="number"
                        className="rounded-xl mt-1"
                        defaultValue={p.declared_salary}
                        onChange={(e) =>
                          setSalaries((s) => ({ ...s, [p.id]: e.target.value }))
                        }
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => verify(p, true)}>
                        Valider banque
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => verify(p, false)}>
                        Refuser
                      </Button>
                    </div>
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
