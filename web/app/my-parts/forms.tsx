"use client";

import Link from "next/link";
import { useActionState } from "react";
import type { Color } from "@/lib/api";
import { addPart, addSetParts, type ActionState } from "./actions";

const initial: ActionState = {};

function Status({ state }: { state: ActionState }) {
  if (state.error) return <p className="text-sm text-accent">{state.error}</p>;
  if (state.message) return <p className="text-sm text-muted">{state.message}</p>;
  return null;
}

export function AddPartForm({ colors }: { colors: Color[] }) {
  const [state, action, pending] = useActionState(addPart, initial);
  return (
    <form action={action} className="card grid gap-3 p-4 md:grid-cols-6">
      <label className="flex flex-col gap-1 text-xs text-muted md:col-span-2">
        Part number
        <input name="part_num" className="input font-mono" placeholder="e.g. 3001" required />
      </label>
      <label className="flex flex-col gap-1 text-xs text-muted md:col-span-2">
        Colour
        <select name="color_id" className="input" defaultValue="" required>
          <option value="" disabled>
            Pick a colour
          </option>
          {colors.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1 text-xs text-muted">
        Quantity
        <input name="quantity" type="number" min={1} defaultValue={1} className="input" required />
      </label>
      <div className="flex items-end">
        <button className="btn w-full" disabled={pending}>
          {pending ? "Adding…" : "Add"}
        </button>
      </div>
      <div className="md:col-span-6">
        <Status state={state} />
      </div>
    </form>
  );
}

export function OwnSetButton({ setNum }: { setNum: string }) {
  const [state, action, pending] = useActionState(addSetParts, initial);
  return (
    <form action={action} className="flex flex-col gap-1">
      <input type="hidden" name="set_num" value={setNum} />
      <button className="btn self-start" disabled={pending}>
        {pending ? "Adding…" : "I own this set: add its parts"}
      </button>
      <Status state={state} />
      {state.message && (
        <Link href="/build" className="text-sm text-accent hover:underline">
          See what you can build →
        </Link>
      )}
    </form>
  );
}
