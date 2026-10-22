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
