import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { getSet, NotFoundError } from "@/lib/api";
import { SetGrid, Skeleton, StatTile } from "@/components/ui";

export default function SetPage(props: PageProps<"/sets/[setNum]">) {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <SetDetail params={props.params} />
    </Suspense>
  );
}

async function SetDetail({ params }: { params: PageProps<"/sets/[setNum]">["params"] }) {
  const { setNum } = await params;
  const data = await getSet(decodeURIComponent(setNum)).catch((error) => {
    if (error instanceof NotFoundError) notFound();
    throw error;
  });
  const { set, related } = data;

  return (
    <div className="flex flex-col gap-8">
      <Link href="/sets" className="text-sm text-muted hover:text-foreground">
        ← Back to search
      </Link>
      <div className="grid gap-6 md:grid-cols-2">
        <div className="card relative aspect-[4/3] bg-white">
          {set.img_url ? (
            <Image src={set.img_url} alt={set.name} fill className="object-contain p-4" />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted">No image</div>
          )}
        </div>
        <div className="flex flex-col gap-4">
          <div>
            <div className="font-mono text-sm text-muted">{set.set_num}</div>
            <h1 className="text-3xl font-semibold tracking-tight">{set.name}</h1>
            {set.theme_name && (
              <div className="mt-2 text-sm">
                {set.parent_theme_id && (
                  <>
                    <Link href={`/themes/${set.parent_theme_id}`} className="text-accent hover:underline">
                      {set.parent_theme_name}
                    </Link>
                    {" › "}
                  </>
                )}
                <Link href={`/themes/${set.theme_id}`} className="text-accent hover:underline">
                  {set.theme_name}
                </Link>
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <StatTile label="Year" value={String(set.year)} />
            <StatTile label="Pieces" value={set.num_parts} />
          </div>
          <a
            href={`https://rebrickable.com/sets/${set.set_num}/`}
            className="text-sm text-muted underline hover:text-foreground"
          >
            View on Rebrickable
          </a>
        </div>
      </div>

      {related.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="font-medium">More from {set.theme_name}</h2>
          <SetGrid sets={related} />
        </section>
      )}
    </div>
  );
}
