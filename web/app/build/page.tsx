import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";
import { getBuildable, type BuildableSet } from "@/lib/api";
import { SetGrid, Skeleton } from "@/components/ui";

export default function BuildPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">What can I build?</h1>
        <p className="text-sm text-muted">
          Sets where you own at least the required quantity of every non-spare part, matching part
          number and colour. Based on{" "}
          <Link href="/my-parts" className="text-accent hover:underline">
            your parts
          </Link>
          .
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-96" />}>
        <Results />
      </Suspense>
    </div>
  );
}

async function Results() {
  const { buildable, more, almost } = await getBuildable();

  if (buildable.length === 0 && almost.length === 0) {
    return (
      <p className="text-sm text-muted">
        None of your parts appear in any set yet.{" "}
        <Link href="/my-parts" className="text-accent hover:underline">
          Add some parts
        </Link>{" "}
        to get started.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="font-medium">
          You can build {buildable.length}
          {more ? "+" : ""} {buildable.length === 1 && !more ? "set" : "sets"}
        </h2>
        {buildable.length > 0 ? (
          <SetGrid sets={buildable} />
        ) : (
          <p className="text-sm text-muted">No complete sets yet. The closest ones are below.</p>
        )}
      </section>

      {almost.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="font-medium">Almost there</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {almost.map((set) => (
              <AlmostRow key={set.set_num} set={set} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function AlmostRow({ set }: { set: BuildableSet }) {
  const percent = Math.floor((set.pieces_owned / set.pieces_required) * 100);
  return (
    <Link
      href={`/sets/${encodeURIComponent(set.set_num)}`}
      className="card flex gap-3 p-3 transition hover:border-accent"
    >
      <div className="relative h-16 w-20 shrink-0 bg-white">
        {set.img_url && (
          <Image src={set.img_url} alt={set.name} fill className="object-contain p-1" />
        )}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="truncate text-sm font-medium">{set.name}</div>
        <div className="h-1.5 overflow-hidden rounded-full bg-border">
          <div className="h-full bg-accent" style={{ width: `${percent}%` }} />
        </div>
        <div className="flex justify-between text-xs text-muted">
          <span>
            {set.pieces_owned.toLocaleString()} of {set.pieces_required.toLocaleString()} pieces (
            {percent}%)
          </span>
          <span>
            missing {set.lots_missing} {set.lots_missing === 1 ? "lot" : "lots"}
          </span>
        </div>
      </div>
    </Link>
  );
}
