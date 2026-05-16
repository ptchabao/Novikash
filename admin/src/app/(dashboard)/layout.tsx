"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { AdminTopNav } from "@/components/admin-top-nav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { staff, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !staff) {
      router.replace("/login");
    }
  }, [loading, staff, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!staff) return null;

  return (
    <div className="min-h-screen bg-background">
      <AdminTopNav />
      <main className="mx-auto max-w-[1600px] px-6 py-8 lg:px-8">{children}</main>
    </div>
  );
}
