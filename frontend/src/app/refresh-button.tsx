"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RefreshButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleRefresh = async () => {
    try {
      setLoading(true);
      setMessage("");

      const res = await fetch("/api/refresh", {
        method: "POST",
      });

      if (!res.ok) {
        setMessage("Refresh failed");
        return;
      }

      setMessage("Stories refreshed");
      router.refresh();
    } catch {
      setMessage("Refresh failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleRefresh}
        disabled={loading}
        className="inline-flex items-center justify-center rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-900 shadow-sm hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-50 dark:hover:bg-zinc-900"
      >
        {loading ? "Refreshing..." : "Refresh stories"}
      </button>

      {message ? (
        <span className="text-xs text-zinc-500 dark:text-zinc-400">{message}</span>
      ) : null}
    </div>
  );
}