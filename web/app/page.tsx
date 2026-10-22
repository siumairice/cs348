import Form from "next/form";
import Link from "next/link";
import { Suspense } from "react";
import { getStats } from "@/lib/api";
import { Skeleton, StatTile, YearChart } from "@/components/ui";

export default function Home() {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-4">
        <h1 className="text-3xl font-semibold tracking-tight">Explore every LEGO set</h1>
        <p className="max-w-2xl text-muted">
          Search the Rebrickable catalogue by name, set number, or theme, then filter by year and
          piece count.
        </p>
        <Form action="/sets" className="flex max-w-xl gap-2">
          <input name="q" className="input" placeholder="Try “Millennium Falcon” or “Technic”" />
          <button className="btn">Search</button>
        </Form>
      </section>

      <Suspense fallback={<Skeleton className="h-96" />}>
        <Overview />
      </Suspense>
    </div>
  );
}

async function Overview() {
  const { totals, per_year, top_themes, biggest_sets } = await getStats();
  const topMax = Math.max(...top_themes.map((t) => t.set_count), 1);

  return (
    <div className="flex flex-col gap-8">
      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatTile label="Sets" value={totals.set_count} />
        <StatTile label="Themes" value={totals.theme_count} />
        <StatTile label="Years" value={`${totals.first_year}–${totals.last_year}`} />
        <StatTile label="Total pieces" value={Number(totals.total_parts)} />
      </section>

      <section className="card p-4">
        <h2 className="mb-3 font-medium">Sets released per year</h2>
        <YearChart data={per_year} />
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="card p-4">
          <h2 className="mb-3 font-medium">Largest themes</h2>
          <ul className="flex flex-col gap-2">
            {top_themes.map((theme) => (
              <li key={theme.id}>
                <Link href={`/themes/${theme.id}`} className="group block text-sm">
                  <div className="flex justify-between">
                    <span className="group-hover:text-accent">{theme.name}</span>
                    <span className="tabular-nums text-muted">{theme.set_count}</span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-border">
                    <div
                      className="h-full rounded-full bg-accent"
                      style={{ width: `${(theme.set_count / topMax) * 100}%` }}
                    />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="card p-4">
          <h2 className="mb-3 font-medium">Biggest sets by piece count</h2>
          <table className="w-full text-sm">
            <tbody>
              {biggest_sets.map((set) => (
                <tr key={set.set_num} className="border-t border-border first:border-0">
                  <td className="py-1.5">
                    <Link href={`/sets/${encodeURIComponent(set.set_num)}`} className="hover:text-accent">
                      {set.name}
                    </Link>
                    <div className="text-xs text-muted">
                      {set.theme_name} · {set.year}
                    </div>
                  </td>
                  <td className="py-1.5 text-right tabular-nums">
                    {set.num_parts?.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
