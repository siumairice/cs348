import Link from "next/link";
import { Suspense } from "react";
import { getUserParts, listColors } from "@/lib/api";
import { Skeleton, StatTile } from "@/components/ui";
import { removePart } from "./actions";
import { AddPartForm } from "./forms";

export default function MyPartsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">My parts</h1>
          <p className="text-sm text-muted">
            Add the pieces you own, then check{" "}
            <Link href="/build" className="text-accent hover:underline">
              what you can build
            </Link>
            . To add a whole set you own, open it from{" "}
            <Link href="/sets" className="text-accent hover:underline">
              Sets
            </Link>
            .
          </p>
        </div>
      </div>
      <Suspense fallback={<Skeleton className="h-96" />}>
        <Collection />
      </Suspense>
    </div>
  );
}

async function Collection() {
  const [{ colors }, { user, parts }] = await Promise.all([listColors(), getUserParts()]);
  const pieces = parts.reduce((sum, p) => sum + p.quantity, 0);

  return (
    <div className="flex flex-col gap-6">
      <AddPartForm colors={colors} />

      <section className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <StatTile label="Signed in as" value={user.username} />
        <StatTile label="Part / colour lots" value={parts.length} />
        <StatTile label="Pieces" value={pieces} />
      </section>

      {parts.length === 0 ? (
        <p className="text-sm text-muted">No parts yet. Add one above.</p>
      ) : (
        <div className="card overflow-x-auto text-sm">
          <table className="w-full min-w-[36rem]">
            <thead className="text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-2 font-normal">Part</th>
                <th className="px-4 py-2 font-normal">Name</th>
                <th className="px-4 py-2 font-normal">Colour</th>
                <th className="px-4 py-2 text-right font-normal">Qty</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {parts.map((p) => (
                <tr key={`${p.part_num}:${p.color_id}`} className="border-t border-border">
                  <td className="px-4 py-2 font-mono">
                    <Link
                      href={`/parts/${encodeURIComponent(p.part_num)}`}
                      className="hover:text-accent"
                    >
                      {p.part_num}
                    </Link>
                  </td>
                  <td className="px-4 py-2">{p.part_name}</td>
                  <td className="px-4 py-2">
                    <span className="flex items-center gap-2">
                      <span
                        className="inline-block h-3 w-3 shrink-0 rounded-sm border border-border"
                        style={{ backgroundColor: `#${p.rgb}` }}
                      />
                      {p.color_name}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums">{p.quantity.toLocaleString()}</td>
                  <td className="px-4 py-2 text-right">
                    <form action={removePart}>
                      <input type="hidden" name="part_num" value={p.part_num} />
                      <input type="hidden" name="color_id" value={p.color_id} />
                      <button className="text-xs text-muted hover:text-accent">Remove</button>
                    </form>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
