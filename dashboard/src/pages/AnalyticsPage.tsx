import { useState } from "react";
import clsx from "clsx";
import PairBarChart from "../components/PairBarChart";
import SpreadChart from "../components/SpreadChart";
import DirectionPie from "../components/DirectionPie";
import ReturnProjections from "../components/ReturnProjections";

const PERIODS = [
  { label: "1d", days: 1 },
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "All", days: 365 },
];

export default function AnalyticsPage() {
  const [days, setDays] = useState(7);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-white">Analytics</h1>
        <div className="flex gap-1">
          {PERIODS.map((p) => (
            <button
              key={p.label}
              onClick={() => setDays(p.days)}
              className={clsx(
                "px-3 py-1 text-xs rounded transition-colors",
                days === p.days
                  ? "bg-accent-blue text-white"
                  : "bg-surface-card text-gray-300 hover:bg-surface-hover border border-gray-700",
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Return projections */}
      <section>
        <h2 className="text-sm font-medium text-gray-400 mb-2 uppercase tracking-wider">
          Theoretical Returns
        </h2>
        <ReturnProjections />
      </section>

      {/* Top pairs */}
      <section className="bg-surface-card rounded border border-gray-700 p-4">
        <h2 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
          Top Pairs by Opportunity Count
        </h2>
        <PairBarChart days={days} />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Frequency */}
        <section className="bg-surface-card rounded border border-gray-700 p-4">
          <h2 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
            Opportunity Frequency
          </h2>
          <SpreadChart days={days} />
        </section>

        {/* Direction */}
        <section className="bg-surface-card rounded border border-gray-700 p-4">
          <h2 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
            Direction Analysis
          </h2>
          <DirectionPie days={days} />
        </section>
      </div>
    </div>
  );
}
