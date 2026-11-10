"use server";

import { refresh } from "next/cache";
import { DEMO_USER_ID, sendForm } from "@/lib/api";

export type ActionState = { error?: string; message?: string };

const partsPath = `/api/users/${DEMO_USER_ID}/parts`;

export async function addPart(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const partNum = String(formData.get("part_num") ?? "").trim();
  const colorId = Number(formData.get("color_id"));
  const quantity = Number(formData.get("quantity"));
  if (!partNum) return { error: "Enter a part number." };
  if (!Number.isInteger(colorId)) return { error: "Pick a colour." };
  if (!Number.isInteger(quantity) || quantity < 1) return { error: "Quantity must be at least 1." };

  const result = await sendForm("POST", partsPath, {
    part_num: partNum,
    color_id: colorId,
    quantity,
  });
  if (!result.ok) return { error: result.error };
  refresh();
  return { message: `Added ${quantity} × ${partNum}.` };
}

export async function removePart(formData: FormData) {
  const partNum = String(formData.get("part_num"));
  const colorId = String(formData.get("color_id"));
  await sendForm("DELETE", `${partsPath}/${encodeURIComponent(partNum)}/${encodeURIComponent(colorId)}`);
  refresh();
}

export async function addSetParts(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const setNum = String(formData.get("set_num"));
  const result = await sendForm("POST", `${partsPath}/from-set/${encodeURIComponent(setNum)}`);
  if (!result.ok) return { error: result.error };
  refresh();
  return { message: "Added this set's parts to your collection." };
}
