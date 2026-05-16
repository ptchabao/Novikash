"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";

export function WalletAdjustDialog({
  open,
  onOpenChange,
  userId,
  userPhone,
  mode,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  userId: number;
  userPhone: string;
  mode: "credit" | "debit";
  onSuccess: () => void;
}) {
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) {
      toast.error("Montant invalide");
      return;
    }
    if (!reason.trim()) {
      toast.error("Motif obligatoire");
      return;
    }
    setLoading(true);
    try {
      const res =
        mode === "credit"
          ? await apiClient.creditWallet(userId, amt, reason)
          : await apiClient.debitWallet(userId, amt, reason);
      toast.success(res.message, {
        description: `Nouveau solde : ${res.new_balance.toLocaleString("fr-FR")} FCFA`,
      });
      setAmount("");
      setReason("");
      onOpenChange(false);
      onSuccess();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {mode === "credit" ? "Crédit manuel" : "Débit manuel"} — {userPhone}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div>
            <Label>Montant (FCFA)</Label>
            <Input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="50000"
            />
          </div>
          <div>
            <Label>Motif</Label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Correction, bonus, remboursement..."
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button
            onClick={submit}
            disabled={loading}
            className={mode === "credit" ? "bg-green-600 hover:bg-green-700" : ""}
            variant={mode === "debit" ? "destructive" : "default"}
          >
            {loading ? "..." : mode === "credit" ? "Créditer" : "Débiter"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
