import Form from "next/form";
import Link from "next/link";
import { Suspense } from "react";
import {
  getPartColors,
  getSetsWithPart,
  NotFoundError,
  type PartColor,
} from "@/lib/api";
import { SetGrid, Skeleton } from "@/components/ui";

const PAGE_SIZE = 48;

export default function FindSetsPage(props: PageProps<"/find-sets">) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Find sets by part</h1>
        <p className="mt-1 text-sm text-muted">
          Found a loose piece? Enter its part number and colour to see which sets it comes from.
          Spare pieces are not counted. Don&apos;t know the number?{" "}
          <Link href="/parts" className="text-accent hover:underline">
            Search parts
          </Link>
          .
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-96" />}>
        <FindSets searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

function first(value: string | string[] | undefined) {
  return (Array.isArray(value) ? value[0] : value)?.trim() || undefined;
}

async function FindSets({
  searchParams,
}: {
  searchParams: PageProps<"/find-sets">["searchParams"];
}) {
  const raw = await searchParams;
  const partNum = first(raw.part);
  const colorId = first(raw.color);
  const page = Math.max(1, Number(first(raw.page)) || 1);

  // Step 1: no part yet, so just the form.
  if (!partNum) return <SearchForm />;

  // Step 2: look up the colours this part comes in, for the drop-down.
  const partColors = await getPartColors(partNum).catch((error) => {
    if (error instanceof NotFoundError) return null;
    throw error;
  });
  if (partColors === null) {
    return (
      <div className="flex flex-col gap-4">
        <SearchForm partNum={partNum} />
        <p className="text-sm text-muted">
          No part numbered <span className="font-mono">{partNum}</span>.{" "}
          <Link href={`/parts?q=${encodeURIComponent(partNum)}`} className="text-accent hover:underline">
            Search parts for “{partNum}”
          </Link>
          .
        </p>
      </div>
    );
  }
  const { part, colors } = partColors;

  return (
    <div className="flex flex-col gap-6">
      <SearchForm partNum={part.part_num} colorId={colorId} colors={colors} />
      <div className="text-sm">
        <Link href={`/parts/${encodeURIComponent(part.part_num)}`} className="font-medium hover:text-accent">
          {part.name}
        </Link>{" "}
        <span className="font-mono text-muted">{part.part_num}</span>
      </div>
      {colorId ? (
        <Results partNum={part.part_num} colorId={colorId} page={page} />
      ) : (
        <ColorChoices partNum={part.part_num} colors={colors} />
      )}
    </div>
  );
}

function SearchForm({
  partNum,
  colorId,
  colors,
}: {
  partNum?: string;
  colorId?: string;
  colors?: PartColor[];
}) {
  return (
    // key resets the uncontrolled inputs when the URL changes
    <Form action="/find-sets" key={`${partNum}:${colorId}`} className="card grid gap-3 p-4 md:grid-cols-6">
      <label className="flex flex-col gap-1 text-xs text-muted md:col-span-2">
        Part number
        <input
          name="part"
          defaultValue={partNum}
          className="input font-mono"
          placeholder="e.g. 3001"
          required
        />
      </label>
      <label className="flex flex-col gap-1 text-xs text-muted md:col-span-3">
        Colour
        {colors ? (
          <select name="color" defaultValue={colorId ?? ""} className="input">
            <option value="">Any colour: show the colours it comes in</option>
            {colors.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.set_count.toLocaleString()} {c.set_count === 1 ? "set" : "sets"})
              </option>
            ))}
          </select>
        ) : (
          <select className="input" disabled defaultValue="">
            <option value="">Enter a part number first</option>
          </select>
        )}
      </label>
      <div className="flex items-end">
        <button className="btn w-full">Find sets</button>
      </div>
    </Form>
  );
}

function ColorChoices({ partNum, colors }: { partNum: string; colors: PartColor[] }) {
  if (colors.length === 0) {
    return <p className="text-sm text-muted">This part does not appear in any set.</p>;
  }
  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-medium">
        Comes in {colors.length} {colors.length === 1 ? "colour" : "colours"}. Pick one:
      </h2>
      <div className="flex flex-wrap gap-2">
        {colors.map((c) => (
          <Link
            key={c.id}
            href={`/find-sets?part=${encodeURIComponent(partNum)}&color=${c.id}`}
            className="card flex items-center gap-2 px-3 py-1.5 text-sm transition hover:border-accent"
          >
            <span
              className="inline-block h-3 w-3 shrink-0 rounded-sm border border-border"
              style={{ backgroundColor: `#${c.rgb}` }}
            />
            {c.name}
            <span className="text-xs text-muted tabular-nums">{c.set_count.toLocaleString()}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

async function Results({ partNum, colorId, page }: { partNum: string; colorId: string; page: number }) {
  const result = await getSetsWithPart(partNum, {
    color_id: colorId,
    limit: String(PAGE_SIZE),
    offset: String((page - 1) * PAGE_SIZE),
  }).catch((error) => {
    if (error instanceof NotFoundError) return null;
    throw error;
  });
  if (result === null) return <p className="text-sm text-muted">Unknown colour.</p>;

  const { color, total, sets } = result;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageHref = (target: number) =>
    `/find-sets?part=${encodeURIComponent(partNum)}&color=${colorId}${target > 1 ? `&page=${target}` : ""}`;

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
        <span className="flex items-center gap-2">
          <span
            className="inline-block h-3 w-3 shrink-0 rounded-sm border border-border"
            style={{ backgroundColor: `#${color.rgb}` }}
          />
          {total.toLocaleString()} {total === 1 ? "set" : "sets"} in {color.name}, newest first
          {total > PAGE_SIZE && ` · page ${page} of ${pageCount}`}
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
      {total === 0 ? (
        <p className="text-sm text-muted">
          No set uses this part in {color.name}.{" "}
          <Link href={`/find-sets?part=${encodeURIComponent(partNum)}`} className="text-accent hover:underline">
            See the colours it comes in
          </Link>
          .
        </p>
      ) : (
        <SetGrid sets={sets} />
      )}
    </section>
  );
}
