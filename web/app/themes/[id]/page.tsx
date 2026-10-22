import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { getTheme, NotFoundError, searchSets } from "@/lib/api";
import { SetGrid, Skeleton, StatTile, YearChart } from "@/components/ui";

export default function ThemePage(props: PageProps<"/themes/[id]">) {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <ThemeDetail params={props.params} />
    </Suspense>
  );
}

async function ThemeDetail({ params }: { params: PageProps<"/themes/[id]">["params"] }) {
  const { id } = await params;
  if (!/^\d+$/.test(id)) notFound();

  const [detail, newest] = await Promise.all([
    getTheme(id).catch((error) => {
      if (error instanceof NotFoundError) notFound();
      throw error;
    }),
    searchSets({ theme_id: id, sort: "year_desc", limit: "12" }),
  ]);
  const { theme, subthemes, stats, per_year } = detail;

  return (
    <div className="flex flex-col gap-8">
      <div>
        {theme.parent_id && (
          <Link href={`/themes/${theme.parent_id}`} className="text-sm text-accent hover:underline">
            {theme.parent_name}
          </Link>
        )}
        <h1 className="text-3xl font-semibold tracking-tight">{theme.name}</h1>
      </div>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatTile label="Sets" value={stats.set_count} />
        <StatTile
          label="Years"
          value={stats.first_year ? `${stats.first_year}–${stats.last_year}` : null}
        />
        <StatTile label="Avg pieces" value={stats.avg_parts === null ? null : Number(stats.avg_parts)} />
        <StatTile label="Largest set" value={stats.max_parts} />
      </section>

      {per_year.length > 0 && (
        <section className="card p-4">
          <h2 className="mb-3 font-medium">Sets per year</h2>
          <YearChart data={per_year} />
        </section>
      )}

      {subthemes.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="font-medium">Subthemes</h2>
          <div className="flex flex-wrap gap-2">
            {subthemes.map((sub) => (
              <Link
                key={sub.id}
                href={`/themes/${sub.id}`}
                className="rounded-full border border-border bg-surface px-3 py-1 text-sm hover:border-accent"
              >
                {sub.name} <span className="text-muted">{sub.set_count}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="flex flex-col gap-3">
        <div className="flex items-baseline justify-between">
          <h2 className="font-medium">Newest sets</h2>
          <Link href={`/sets?theme_id=${theme.id}`} className="text-sm text-accent hover:underline">
            See all {newest.total.toLocaleString()} →
          </Link>
        </div>
        <SetGrid sets={newest.sets} />
      </section>
    </div>
  );
}
