import Form from "next/form";
import Link from "next/link";
import { Suspense } from "react";
import { listThemes } from "@/lib/api";
import { Skeleton } from "@/components/ui";

export default function ThemesPage(props: PageProps<"/themes">) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">Themes</h1>
      <Suspense fallback={<Skeleton className="h-96" />}>
        <ThemeTable searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

async function ThemeTable({ searchParams }: { searchParams: PageProps<"/themes">["searchParams"] }) {
  const raw = (await searchParams).q;
  const q = (Array.isArray(raw) ? raw[0] : raw) ?? "";
  const { themes } = await listThemes(q);

  return (
    <div className="flex flex-col gap-4">
      <Form action="/themes" key={q} className="flex max-w-md gap-2">
        <input name="q" defaultValue={q} className="input" placeholder="Filter themes" />
        <button className="btn">Filter</button>
      </Form>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-2">Theme</th>
              <th className="px-4 py-2">Parent</th>
              <th className="px-4 py-2 text-right">Sets</th>
              <th className="px-4 py-2 text-right">Years</th>
            </tr>
          </thead>
          <tbody>
            {themes.map((theme) => (
              <tr key={theme.id} className="border-t border-border">
                <td className="px-4 py-2">
                  <Link href={`/themes/${theme.id}`} className="hover:text-accent">
                    {theme.name}
                  </Link>
                </td>
                <td className="px-4 py-2 text-muted">
                  {theme.parent_id && (
                    <Link href={`/themes/${theme.parent_id}`} className="hover:text-accent">
                      {theme.parent_name}
                    </Link>
                  )}
                </td>
                <td className="px-4 py-2 text-right tabular-nums">{theme.set_count}</td>
                <td className="px-4 py-2 text-right tabular-nums text-muted">
                  {theme.first_year ? `${theme.first_year}–${theme.last_year}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {themes.length === 0 && <p className="p-4 text-sm text-muted">No themes match.</p>}
      </div>
    </div>
  );
}
