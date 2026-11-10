import Image from "next/image";
import Link from "next/link";
import type { SetSummary, YearCount } from "@/lib/api";

export function StatTile({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">
        {typeof value === "number" ? value.toLocaleString() : (value ?? "—")}
      </div>
    </div>
  );
}

export function SetCard({ set }: { set: SetSummary }) {
  return (
    <Link
      href={`/sets/${encodeURIComponent(set.set_num)}`}
      className="card flex flex-col overflow-hidden transition hover:border-accent"
    >
      <div className="relative aspect-[4/3] bg-white">
        {set.img_url ? (
          <Image src={set.img_url} alt={set.name} fill className="object-contain p-2" />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted">No image</div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1 border-t border-border p-3">
        <div className="line-clamp-2 text-sm font-medium">{set.name}</div>
        <div className="mt-auto flex justify-between text-xs text-muted">
          <span>
            {set.year} · {set.num_parts?.toLocaleString() ?? "?"} pcs
          </span>
          <span className="font-mono">{set.set_num}</span>
        </div>
        {set.theme_name && (
          <div className="truncate text-xs text-muted">
            {set.parent_theme_name ? `${set.parent_theme_name} › ` : ""}
            {set.theme_name}
          </div>
        )}
      </div>
    </Link>
  );
}

export function SetGrid({ sets }: { sets: SetSummary[] }) {
  if (sets.length === 0) {
    return <p className="text-sm text-muted">No sets match.</p>;
  }
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {sets.map((set) => (
        <SetCard key={set.set_num} set={set} />
      ))}
    </div>
  );
}

export function YearChart({ data }: { data: YearCount[] }) {
  if (data.length === 0) return null;
  const max = Math.max(...data.map((d) => d.set_count));
  return (
    <div>
      <div className="flex h-40 items-end gap-px">
        {data.map((d) => (
          <div
            key={d.year}
            title={`${d.year}: ${d.set_count} sets`}
            className="flex-1 rounded-t-sm bg-accent/80 hover:bg-accent"
            style={{ height: `${Math.max(2, (d.set_count / max) * 100)}%` }}
          />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-xs text-muted">
        <span>{data[0].year}</span>
        <span>{data[data.length - 1].year}</span>
      </div>
    </div>
  );
}

export function Skeleton({ className = "h-40" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-border/60 ${className}`} />;
}

export function ApiError() {
  return (
    <div className="card border-accent bg-accent-soft p-4 text-sm">
      Could not reach the API. Make sure FastAPI is running (
      <code className="font-mono">docker compose up</code>) and <code>API_URL</code> points at it.
    </div>
  );
}

type PartRow = { part_num: string; name: string; category_name: string; related_count?: number };

// Each row is a single link so clicking anywhere on it opens the part.
export function PartList({ parts, showCount = false }: { parts: PartRow[]; showCount?: boolean }) {
  const cols = showCount
    ? "grid-cols-[9rem_minmax(0,1fr)_12rem_5rem]"
    : "grid-cols-[9rem_minmax(0,1fr)_12rem]";
  return (
    <div className="card overflow-x-auto text-sm">
      <div className="min-w-[36rem]">
        <div className={`grid ${cols} text-left text-xs uppercase tracking-wide text-muted`}>
          <div className="px-4 py-2">Part</div>
          <div className="px-4 py-2">Name</div>
          <div className="px-4 py-2">Category</div>
          {showCount && <div className="px-4 py-2 text-right">Related</div>}
        </div>
        {parts.map((part, i) => (
          <Link
            key={`${part.part_num}:${i}`}
            href={`/parts/${encodeURIComponent(part.part_num)}`}
            className={`grid ${cols} border-t border-border hover:bg-accent-soft hover:text-accent`}
          >
            <div className="px-4 py-2 font-mono">{part.part_num}</div>
            <div className="px-4 py-2">{part.name}</div>
            <div className="px-4 py-2 text-muted">{part.category_name}</div>
            {showCount && <div className="px-4 py-2 text-right tabular-nums">{part.related_count}</div>}
          </Link>
        ))}
      </div>
    </div>
  );
}
