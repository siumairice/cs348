"use client";

import { ApiError } from "@/components/ui";

export default function Error({ retry }: { error: unknown; retry: () => void }) {
  return (
    <div className="flex flex-col items-start gap-3">
      <ApiError />
      <button className="btn" onClick={() => retry()}>
        Try again
      </button>
    </div>
  );
}
