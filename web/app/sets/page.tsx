import Form from "next/form";
import Link from "next/link";
import { Suspense } from "react";
import { listThemes, searchSets } from "@/lib/api";
import { SetGrid, Skeleton } from "@/components/ui";

const PAGE_SIZE = 48;
const FILTERS = ["q", "theme_id", "year_min", "year_max", "parts_min", "parts_max", "sort"] as const;
const SORTS = [
  { value: "year_desc", label: "Newest first" },
  { value: "year_asc", label: "Oldest first" },
  { value: "parts_desc", label: "Most pieces" },
  { value: "parts_asc", label: "Fewest pieces" },
  { value: "name", label: "Name (A–Z)" },
];

type Filters = Partial<Record<(typeof FILTERS)[number], string>>;

export default function SetsPage(props: PageProps<"/sets">) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">Search sets</h1>
      <Suspense fallback={<Skeleton className="h-96" />}>
        <SetSearch searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

async function SetSearch({
  searchParams,
}: {
  searchParams: PageProps<"/sets">["searchParams"];
}) {
  const raw = await searchParams;
  const filters: Filters = {};
  for (const key of FILTERS) filters[key] = first(raw[key]) || undefined;
  const page = Math.max(1, Number(first(raw.page)) || 1);

  const [{ themes }, results] = await Promise.all([
    listThemes(),
    searchSets({
      ...filters,
      limit: String(PAGE_SIZE),
      offset: String((page - 1) * PAGE_SIZE),
    }),
  ]);

  const themeOptions = themes
    .map((t) => ({ id: t.id, label: t.parent_name ? `${t.parent_name} › ${t.name}` : t.name }))
    .sort((a, b) => a.label.localeCompare(b.label));
  const pageCount = Math.max(1, Math.ceil(results.total / PAGE_SIZE));

  const pageHref = (target: number) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) if (value) params.set(key, value);
    if (target > 1) params.set("page", String(target));
    return `/sets?${params}`;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* key resets the uncontrolled inputs when the URL changes */}
      <Form action="/sets" key={JSON.stringify(filters)} className="card grid gap-3 p-4 md:grid-cols-6">
        <label className="flex flex-col gap-1 text-xs text-muted md:col-span-3">
          Name, set number, or theme
          <input name="q" defaultValue={filters.q} className="input" placeholder="e.g. Hogwarts" />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted md:col-span-2">
          Theme
          <select name="theme_id" defaultValue={filters.theme_id ?? ""} className="input">
            <option value="">Any theme</option>
            {themeOptions.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Sort
          <select name="sort" defaultValue={filters.sort ?? "year_desc"} className="input">
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <RangeInputs label="Year" name="year" min={filters.year_min} max={filters.year_max} />
        <RangeInputs label="Pieces" name="parts" min={filters.parts_min} max={filters.parts_max} />
        <div className="flex items-end gap-2 md:col-span-2">
          <button className="btn flex-1">Apply</button>
          <Link href="/sets" className="rounded-md border border-border px-4 py-2 text-sm">
            Reset
          </Link>
        </div>
      </Form>

      <div className="flex items-center justify-between text-sm text-muted">
        <span>
          {results.total.toLocaleString()} sets
          {results.total > 0 && ` · page ${page} of ${pageCount}`}
        </span>
        <div className="flex gap-2">
          {page > 1 && (
            <Link href={pageHref(page - 1)} className="hover:text-foreground">
              ← Previous
            </Link>
          )}
          {page < pageCount && (
            <Link href={pageHref(page + 1)} className="hover:text-foreground">
              Next →
            </Link>
          )}
        </div>
      </div>

      <SetGrid sets={results.sets} />
    </div>
  );
}

function RangeInputs({
  label,
  name,
  min,
  max,
}: {
  label: string;
  name: string;
  min?: string;
  max?: string;
}) {
  return (
    <fieldset className="flex flex-col gap-1 text-xs text-muted md:col-span-2">
      <legend className="mb-1">{label}</legend>
      <div className="flex items-center gap-2">
        <input name={`${name}_min`} type="number" defaultValue={min} placeholder="min" className="input" />
        <span>–</span>
        <input name={`${name}_max`} type="number" defaultValue={max} placeholder="max" className="input" />
      </div>
    </fieldset>
  );
}
