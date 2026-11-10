"use server";

import { revalidatePath } from "next/cache";
import { markCompleted, removeCompleted } from "@/lib/api";

function refreshPages(setNum: string) {
  revalidatePath("/completed");
  revalidatePath(`/sets/${encodeURIComponent(setNum)}`);
}

export async function markCompletedAction(setNum: string) {
  await markCompleted(setNum);
  refreshPages(setNum);
}

export async function removeCompletedAction(setNum: string) {
  await removeCompleted(setNum);
  refreshPages(setNum);
}
