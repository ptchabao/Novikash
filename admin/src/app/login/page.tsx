"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const { login, staff, loading } = useAuth();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && staff) {
    if (typeof window !== "undefined") window.location.href = "/";
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(phone, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Échec de connexion");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-gradient-to-br from-primary/90 to-orange-600 p-12 text-white">
        <div>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/20 text-xl font-bold backdrop-blur">
            N
          </div>
          <h2 className="mt-12 text-4xl font-bold leading-tight">
            Pilotez NoviKash
            <br />
            en toute confiance
          </h2>
          <p className="mt-4 max-w-md text-white/80">
            Console admin — prêts, wallets, transactions et conformité KYC sur une interface unifiée.
          </p>
        </div>
        <p className="text-sm text-white/50">© NoviKash — La Finance avec un Cœur</p>
      </div>

      <div className="flex flex-1 items-center justify-center bg-background p-6">
        <Card className="w-full max-w-md border-border shadow-xl rounded-2xl">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-2xl font-bold text-primary-foreground lg:hidden">
              N
            </div>
            <CardTitle className="text-2xl font-bold">Connexion</CardTitle>
            <CardDescription>Accès réservé au personnel autorisé</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive" className="rounded-xl">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-2">
                <Label htmlFor="phone">Téléphone</Label>
                <Input
                  id="phone"
                  className="rounded-xl h-11"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+228..."
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Mot de passe</Label>
                <Input
                  id="password"
                  type="password"
                  className="rounded-xl h-11"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full h-11 rounded-xl text-base" disabled={submitting}>
                {submitting ? "Connexion..." : "Se connecter"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
