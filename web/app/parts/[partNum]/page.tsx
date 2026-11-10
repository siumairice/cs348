import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { getPart, NotFoundError, type RelatedPart } from "@/lib/api";
import { PartList, Skeleton } from "@/components/ui";

// Rebrickable rows read "child <rel_type> parent". The label depends on which
// side the part being viewed is on. Keep this order in sync with the
// FIELD(rel_type, ...) ordering in app.py's get_part.
const LABELS: [key: string, label: string][] = [
  ["P:parent", "Printed versions"],
  ["P:child", "Print of"],
  ["T:parent", "Patterned versions"],
  ["T:child", "Pattern of"],
  ["M:parent", "Alternate moulds"],
  ["M:child", "Alternate mould of"],
  ["A:parent", "Alternates"],
  ["A:child", "Alternate of"],
  ["B:parent", "Sub-parts"],
  ["B:child", "Sub-part of"],
  ["R:parent", "Paired with"],
  ["R:child", "Paired with"],
];

const PAGE_SIZE = 100;
const labelFor = new Map(LABELS);
const labelOf = (row: { rel_type: string; role: string }) =>
  labelFor.get(`${row.rel_type}:${row.role}`) ?? "Related";

// The API returns rows already in LABELS order, so grouping in the order rows
// arrive keeps a group that spans two pages at the end of one and start of the next.
function groupRelated(related: RelatedPart[]) {
  const groups = new Map<string, RelatedPart[]>();
  for (const row of related) {
    const label = labelOf(row);
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label)!.push(row);
  }
  return [...groups];
}

export default function PartPage(props: PageProps<"/parts/[partNum]">) {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <PartDetail params={props.params} searchParams={props.searchParams} />
    </Suspense>
  );
}

async function PartDetail({
  params,
  searchParams,
}: {
  params: PageProps<"/parts/[partNum]">["params"];
  searchParams: PageProps<"/parts/[partNum]">["searchParams"];
}) {
  const { partNum } = await params;
  const rawPage = (await searchParams).page;
  const page = Math.max(1, Number(Array.isArray(rawPage) ? rawPage[0] : rawPage) || 1);
  const { part, total, counts, related } = await getPart(decodeURIComponent(partNum), {
    limit: String(PAGE_SIZE),
    offset: String((page - 1) * PAGE_SIZE),
  }).catch((error) => {
    if (error instanceof NotFoundError) notFound();
    throw error;
  });
  const groups = groupRelated(related);
  const groupTotals = new Map<string, number>();
  for (const row of counts) {
    groupTotals.set(labelOf(row), (groupTotals.get(labelOf(row)) ?? 0) + row.count);
  }
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageHref = (target: number) =>
    `/parts/${encodeURIComponent(part.part_num)}${target > 1 ? `?page=${target}` : ""}`;
  const pager = total > PAGE_SIZE && (
    <Pager page={page} pageCount={pageCount} total={total} pageHref={pageHref} />
  );

  return (
    <div className="flex flex-col gap-8">
      <div>
        <Link href="/parts" className="text-sm text-accent hover:underline">
          Parts
        </Link>
        <h1 className="text-3xl font-semibold tracking-tight">{part.name}</h1>
        <div className="mt-1 text-sm text-muted">
          <span className="font-mono">{part.part_num}</span> · {part.category_name}
          {part.part_material && ` · ${part.part_material}`}
        </div>
        <Link
          href={`/find-sets?part=${encodeURIComponent(part.part_num)}`}
          className="mt-2 inline-block text-sm text-accent hover:underline"
        >
          Find sets with this part →
        </Link>
      </div>

      {total === 0 ? (
        <p className="text-sm text-muted">No related parts.</p>
      ) : (
        <>
          {pager}
          {groups.length === 0 && <p className="text-sm text-muted">No related parts on this page.</p>}
          {groups.map(([label, rows]) => (
            <section key={label} className="flex flex-col gap-3">
              <h2 className="font-medium">
                {label}{" "}
                <span className="text-muted">({(groupTotals.get(label) ?? rows.length).toLocaleString()})</span>
              </h2>
              <PartList parts={rows} />
            </section>
          ))}
          {pager}
        </>
      )}
    </div>
  );
}

function Pager({
  page,
  pageCount,
  total,
  pageHref,
}: {
  page: number;
  pageCount: number;
  total: number;
  pageHref: (target: number) => string;
}) {
  return (
    <div className="flex items-center justify-between text-sm text-muted">
      <span>
        {total.toLocaleString()} related parts · page {page} of {pageCount}
      </span>
      <div className="flex gap-4">
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
  );
}
