import { MoreHorizontal, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";

export function KpiCard({
  title,
  value,
  growth,
  growthLabel,
}: {
  title: string;
  value: string | number;
  growth?: string;
  growthLabel?: string;
}) {
  return (
    <div className="dashboard-card relative flex flex-col p-5">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <Button variant="ghost" size="icon" className="-mr-2 -mt-1 h-8 w-8 text-muted-foreground">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </div>
      <p className="mt-3 text-2xl font-bold tracking-tight md:text-3xl">{value}</p>
      {(growth || growthLabel) && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {growth && (
            <span className="kpi-growth">
              <TrendingUp className="h-3.5 w-3.5" />
              {growth}
            </span>
          )}
          {growthLabel && (
            <span className="text-xs text-muted-foreground">{growthLabel}</span>
          )}
        </div>
      )}
    </div>
  );
}

export function formatFcfa(n: number) {
  return new Intl.NumberFormat("fr-FR").format(Math.round(n)) + " FCFA";
}
