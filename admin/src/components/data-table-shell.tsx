import { Search, SlidersHorizontal } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function DataTableShell({
  title,
  searchPlaceholder = "Rechercher...",
  searchValue,
  onSearchChange,
  filters,
  children,
}: {
  title: string;
  searchPlaceholder?: string;
  searchValue?: string;
  onSearchChange?: (v: string) => void;
  filters?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="dashboard-card overflow-hidden">
      <div className="flex flex-col gap-4 border-b border-border p-5 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="text-lg font-semibold">{title}</h3>
        <div className="flex flex-wrap items-center gap-2">
          {onSearchChange && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="w-full min-w-[220px] rounded-xl border-border bg-muted/30 pl-9 sm:w-64"
                placeholder={searchPlaceholder}
                value={searchValue}
                onChange={(e) => onSearchChange(e.target.value)}
              />
            </div>
          )}
          {filters}
          <Button variant="outline" size="sm" className="rounded-xl gap-2">
            <SlidersHorizontal className="h-4 w-4" />
            Filtrer
          </Button>
        </div>
      </div>
      <div className="overflow-x-auto">{children}</div>
    </div>
  );
}
