import { connection } from "next/server";

// Server-side only: the browser never talks to FastAPI directly.
const API_URL = process.env.API_URL ?? "http://localhost:8000";

export type SetSummary = {
  set_num: string;
  name: string;
  year: number;
  num_parts: number | null;
  img_url: string | null;
  theme_id?: number | null;
  theme_name?: string | null;
  parent_theme_name?: string | null;
};

export type SetDetail = SetSummary & {
  parent_theme_id: number | null;
  completed_at: string | null;
};

export type CompletedSet = {
  set_num: string;
  name: string;
  completed_at: string;
};

export type Theme = {
  id: number;
  name: string;
  parent_id: number | null;
  parent_name: string | null;
  set_count: number;
  first_year: number | null;
  last_year: number | null;
};

export type YearCount = { year: number; set_count: number; avg_parts?: number | null };

export type SetSearch = {
  total: number;
  limit: number;
  offset: number;
  sets: SetSummary[];
};

export type ThemeDetail = {
  theme: { id: number; name: string; parent_id: number | null; parent_name: string | null };
  subthemes: { id: number; name: string; set_count: number }[];
  stats: {
    set_count: number;
    first_year: number | null;
    last_year: number | null;
    avg_parts: number | null;
    max_parts: number | null;
  };
  per_year: YearCount[];
};

export type Stats = {
  totals: {
    set_count: number;
    theme_count: number;
    first_year: number;
    last_year: number;
    total_parts: number;
  };
  per_year: YearCount[];
  top_themes: { id: number; name: string; set_count: number }[];
  biggest_sets: SetSummary[];
};

export class NotFoundError extends Error {}

async function get<T>(path: string, params?: Record<string, string | undefined>): Promise<T> {
  await connection();
  const url = new URL(path, API_URL);
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value) url.searchParams.set(key, value);
  }
  const response = await fetch(url);
  if (response.status === 404) throw new NotFoundError(path);
  if (!response.ok) {
    throw new Error(`API ${url.pathname} failed with ${response.status}`);
  }
  return response.json();
}

export const searchSets = (params: Record<string, string | undefined>) =>
  get<SetSearch>("/api/sets", params);

export const getSet = (setNum: string) =>
  get<{ set: SetDetail; related: SetSummary[] }>(`/api/sets/${encodeURIComponent(setNum)}`);

export const listThemes = (q?: string) =>
  get<{ themes: Theme[] }>("/api/themes", { q });

export const getTheme = (id: string) =>
  get<ThemeDetail>(`/api/themes/${encodeURIComponent(id)}`);

export const getStats = () => get<Stats>("/api/stats");

export const listCompleted = () => get<{ sets: CompletedSet[] }>("/api/completed");

async function send(method: "POST" | "DELETE", path: string, okStatuses: number[] = []) {
  const url = new URL(path, API_URL);
  const response = await fetch(url, { method });
  if (!response.ok && !okStatuses.includes(response.status)) {
    throw new Error(`API ${method} ${url.pathname} failed with ${response.status}`);
  }
}

// 409 means the set is already completed (double click or stale page), so it counts as success.
export const markCompleted = (setNum: string) =>
  send("POST", `/api/completed/${encodeURIComponent(setNum)}`, [409]);

export const removeCompleted = (setNum: string) =>
  send("DELETE", `/api/completed/${encodeURIComponent(setNum)}`);

export type PartSummary = {
  part_num: string;
  name: string;
  category_name: string;
  related_count: number;
};

export type RelType = "P" | "T" | "M" | "A" | "B" | "R";

export type RelatedPart = {
  rel_type: RelType;
  // Which side of the relationship the requested part is on.
  role: "child" | "parent";
  part_num: string;
  name: string;
  category_name: string;
};

export type PartDetail = {
  part: {
    part_num: string;
    name: string;
    part_material: string | null;
    category_id: number;
    category_name: string;
  };
  total: number;
  limit: number;
  offset: number;
  // Totals per relationship group, across all pages.
  counts: { rel_type: RelType; role: RelatedPart["role"]; count: number }[];
  related: RelatedPart[];
};

export const searchParts = (q?: string) =>
  get<{ parts: PartSummary[] }>("/api/parts", { q });

export const getPart = (partNum: string, params?: { limit?: string; offset?: string }) =>
  get<PartDetail>(`/api/parts/${encodeURIComponent(partNum)}`, params);

// Feature 3: a user's parts and the sets they can build.
// There is no login yet, so every page acts as the demo user seeded by db/schema.sql.
export const DEMO_USER_ID = 1;

export type Color = { id: number; name: string; rgb: string; is_trans: number };

export type OwnedPart = {
  part_num: string;
  part_name: string;
  color_id: number;
  color_name: string;
  rgb: string;
  quantity: number;
};

export type User = { id: number; username: string };

export type BuildableSet = SetSummary & {
  pieces_required: number;
  pieces_owned: number;
  // Distinct part/colour lots the user has too few of (0 = buildable).
  lots_missing: number;
};

export const listColors = () => get<{ colors: Color[] }>("/api/colors");

export const getUserParts = (userId = DEMO_USER_ID) =>
  get<{ user: User; parts: OwnedPart[] }>(`/api/users/${userId}/parts`);

export const getBuildable = (userId = DEMO_USER_ID) =>
  get<{
    user: User;
    buildable: BuildableSet[];
    // True when there are more buildable sets than were returned.
    more: boolean;
    almost: BuildableSet[];
  }>(
    `/api/users/${userId}/buildable`,
  );

// Writes go through Server Actions, which call this. Returns the API's error
// message instead of throwing, so forms can show it.
export async function sendForm(
  method: "POST" | "DELETE",
  path: string,
  body?: unknown,
): Promise<{ ok: true } | { ok: false; error: string }> {
  const response = await fetch(new URL(path, API_URL), {
    method,
    headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (response.ok) return { ok: true };
  const data = await response.json().catch(() => null);
  const detail = data?.detail;
  const error =
    typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((d: { msg?: string }) => d.msg).join(", ")
        : `Request failed with ${response.status}`;
  return { ok: false, error };
}
