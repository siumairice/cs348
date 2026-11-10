import Link from "next/link";
import { Suspense } from "react";
import { listCompleted } from "@/lib/api";
import { Skeleton } from "@/components/ui";
import { SubmitButton } from "@/components/submit-button";
import { removeCompletedAction } from "./actions";

export default function CompletedPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">My Completed Sets</h1>
      <Suspense fallback={<Skeleton className="h-64" />}>
        <CompletedTable />
      </Suspense>
    </div>
  );
}

async function CompletedTable() {
  const { sets } = await listCompleted();

  if (sets.length === 0) {
    return (
      <p className="text-sm text-muted">
        No completed sets yet.{" "}
        <Link href="/sets" className="text-accent hover:underline">
          Browse sets
        </Link>{" "}
        and mark the ones you&apos;ve built.
      </p>
    );
  }

  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-left text-xs uppercase tracking-wide text-muted">
          <tr>
            <th className="px-4 py-2">Set #</th>
            <th className="px-4 py-2">Name</th>
            <th className="px-4 py-2">Completed</th>
            <th className="px-4 py-2" />
          </tr>
        </thead>
        <tbody>
          {sets.map((set) => (
            <tr key={set.set_num} className="border-t border-border">
              <td className="px-4 py-2 font-mono">
                <Link href={`/sets/${encodeURIComponent(set.set_num)}`} className="text-accent hover:underline">
                  {set.set_num}
                </Link>
              </td>
              <td className="px-4 py-2">{set.name}</td>
              <td className="px-4 py-2 tabular-nums">{set.completed_at.slice(0, 10)}</td>
              <td className="px-4 py-2 text-right">
                <form action={removeCompletedAction.bind(null, set.set_num)}>
                  <SubmitButton pendingText="Removing…">Remove</SubmitButton>
                </form>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
