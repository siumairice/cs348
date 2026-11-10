import Form from "next/form";
import { Suspense } from "react";
import { searchParts } from "@/lib/api";
import { PartList, Skeleton } from "@/components/ui";

export default function PartsPage(props: PageProps<"/parts">) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Parts</h1>
        <p className="mt-1 text-sm text-muted">
          Look up a part to see its prints, patterns, alternate moulds, and sub-parts.
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-96" />}>
        <PartTable searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

async function PartTable({ searchParams }: { searchParams: PageProps<"/parts">["searchParams"] }) {
  const raw = (await searchParams).q;
  const q = (Array.isArray(raw) ? raw[0] : raw) ?? "";
  const { parts } = await searchParts(q);

  return (
    <div className="flex flex-col gap-4">
      <Form action="/parts" key={q} className="flex max-w-md gap-2">
        <input
          name="q"
          defaultValue={q}
          className="input"
          placeholder="Part number or name, e.g. 2339 or arch"
        />
        <button className="btn">Search</button>
      </Form>
      {parts.length === 0 ? (
        <p className="text-sm text-muted">No parts match.</p>
      ) : (
        <PartList parts={parts} showCount />
      )}
    </div>
  );
}
