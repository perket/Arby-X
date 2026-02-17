import { useRef, useEffect, useState } from "react";
import clsx from "clsx";
import { useLive } from "../api/hooks";
import type { LiveComparison } from "../types";

export default function ComparisonTicker() {
  const { data } = useLive();
  const prevData = useRef<Record<string, LiveComparison>>({});
  const [flashing, setFlashing] = useState<Record<string, "green" | "red" | null>>({});

  useEffect(() => {
    if (!data) return;
    const newFlashes: Record<string, "green" | "red" | null> = {};
    for (const [key, val] of Object.entries(data)) {
      const prev = prevData.current[key];
      if (prev && prev.spread_pct !== val.spread_pct) {
        newFlashes[key] = val.spread_pct > prev.spread_pct ? "green" : "red";
      }
    }
    prevData.current = data;
    setFlashing(newFlashes);
    const timer = setTimeout(() => setFlashing({}), 600);
    return () => clearTimeout(timer);
  }, [data]);

  if (!data) {
    return <div className="text-gray-500 text-sm">Waiting for data...</div>;
  }

  const entries = Object.entries(data).sort((a, b) => b[1].spread_pct - a[1].spread_pct);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
      {entries.map(([key, comp]) => {
        const stale = (Date.now() / 1000 - comp.ts) > 10;
        return (
          <div
            key={key}
            className={clsx(
              "bg-surface-card rounded p-3 border border-gray-700 transition-colors",
              flashing[key] === "green" && "animate-flash-green",
              flashing[key] === "red" && "animate-flash-red",
              stale && "opacity-40",
            )}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-white">{comp.route_label}</span>
              <span
                className={clsx(
                  "text-xs px-1.5 py-0.5 rounded",
                  comp.route_type === "direct"
                    ? "bg-accent-blue/20 text-accent-blue"
                    : "bg-accent-purple/20 text-accent-purple",
                )}
              >
                {comp.route_type === "direct" ? "D" : "ML"}
              </span>
            </div>
            <div
              className={clsx(
                "text-lg font-bold tabular-nums",
                comp.spread_pct > 0.5
                  ? "text-accent-green"
                  : comp.spread_pct > 0
                    ? "text-accent-amber"
                    : "text-gray-400",
              )}
            >
              {comp.spread_pct.toFixed(4)}%
            </div>
            <div className="flex justify-between mt-1 text-xs text-gray-400">
              <span>
                Buy: {comp.buy_rate.toFixed(8)}
              </span>
              <span>
                Sell: {comp.sell_rate.toFixed(8)}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {comp.buy_exchange} &rarr; {comp.sell_exchange}
            </div>
          </div>
        );
      })}
    </div>
  );
}
