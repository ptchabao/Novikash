"use client";

import { Download, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/contexts/auth-context";

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Bonjour";
  if (h < 18) return "Bon après-midi";
  return "Bonsoir";
}

export function PageHeader({
  title,
  subtitle,
  showExport = false,
  showPeriod = false,
}: {
  title?: string;
  subtitle?: string;
  showExport?: boolean;
  showPeriod?: boolean;
}) {
  const { staff } = useAuth();
  const dateStr = new Date().toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
          {title ?? `${getGreeting()}, Admin !`}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {subtitle ?? (
            <>
              {dateStr}
              {staff?.role && (
                <span className="ml-2 rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground">
                  {staff.role}
                </span>
              )}
            </>
          )}
        </p>
      </div>
      {(showExport || showPeriod) && (
        <div className="flex items-center gap-2">
          {showPeriod && (
            <Select defaultValue="month">
              <SelectTrigger className="w-[140px] rounded-xl border-border bg-card">
                <SelectValue placeholder="Période" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="week">Cette semaine</SelectItem>
                <SelectItem value="month">Ce mois</SelectItem>
                <SelectItem value="year">Cette année</SelectItem>
              </SelectContent>
            </Select>
          )}
          {showExport && (
            <Button className="rounded-xl gap-2 shadow-sm">
              <Download className="h-4 w-4" />
              Exporter
              <ChevronDown className="h-3.5 w-3.5 opacity-70" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
