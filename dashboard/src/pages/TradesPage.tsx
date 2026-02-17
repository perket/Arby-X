import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import { format } from "date-fns";
import { useTrades, useBalances } from "../api/hooks";

const COLORS: Record<string, string> = {
  BTC: "#f7931a",
  ETH: "#627eea",
  XLM: "#14b6e7",
  XRP: "#23292f",
  ADA: "#0d1e30",
};

export default function TradesPage() {
  const [page, setPage] = useState(1);
  const [balDays, setBalDays] = useState(7);
  const { data: trades } = useTrades(page);
  const { data: balances } = useBalances(balDays);

  // Group balances by timestamp for multi-line chart
  const chartData: Record<string, Record<string, number>> = {};
  const currencies = new Set<string>();
  for (const b of balances ?? []) {
    const key = b.ts.slice(0, 19);
    if (!chartData[key]) chartData[key] = { ts: Date.parse(b.ts) } as any;
    chartData[key][b.currency] = b.balance;
    currencies.add(b.currency);
  }
  const chartArray = Object.entries(chartData)
    .map(([ts, vals]) => ({ ts, ...vals }))
    .sort((a, b) => a.ts.localeCompare(b.ts));

  const totalPages = trades ? Math.ceil(trades.total / trades.per_page) : 1;

  return (
    <div className="space-y-6">
      {/* Balance history chart */}
      <section className="bg-surface-card rounded border border-gray-700 p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
            Balance History
          </h2>
          <div className="flex gap-1">
            {[1, 7, 30].map((d) => (
              <button
                key={d}
                onClick={() => setBalDays(d)}
                className={`px-2 py-1 text-xs rounded ${
                  balDays === d
                    ? "bg-accent-blue text-white"
                    : "bg-surface text-gray-300 hover:bg-surface-hover border border-gray-700"
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>
        {chartArray.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartArray}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="ts"
                tick={{ fill: "#9CA3AF", fontSize: 10 }}
                tickFormatter={(v) => v.slice(5, 16)}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: 4,
                  color: "#e5e7eb",
                }}
              />
              <Legend wrapperStyle={{ color: "#9CA3AF", fontSize: 12 }} />
              {[...currencies].sort().map((c) => (
                <Line
                  key={c}
                  type="monotone"
                  dataKey={c}
                  stroke={COLORS[c] ?? "#6b7280"}
                  strokeWidth={2}
                  dot={false}
                  name={c}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-gray-500 text-sm py-8 text-center">No balance data</div>
        )}
      </section>

      {/* Trade table */}
      <section>
        <h2 className="text-sm font-medium text-gray-400 mb-2 uppercase tracking-wider">
          Executed Trades
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400 text-xs">
                <th className="text-left py-2 px-2">ID</th>
                <th className="text-left py-2 px-2">Time</th>
                <th className="text-left py-2 px-2">Market</th>
                <th className="text-left py-2 px-2">Legs</th>
              </tr>
            </thead>
            <tbody>
              {(trades?.items ?? []).map((trade) => (
                <tr
                  key={trade.id}
                  className="border-b border-gray-800 hover:bg-surface-hover transition-colors"
                >
                  <td className="py-2 px-2 text-gray-400">{trade.id}</td>
                  <td className="py-2 px-2 text-gray-300 tabular-nums whitespace-nowrap">
                    {format(new Date(trade.ts), "MM-dd HH:mm:ss")}
                  </td>
                  <td className="py-2 px-2 text-white font-medium">{trade.market}</td>
                  <td className="py-2 px-2">
                    <div className="space-y-1">
                      {trade.legs.map((leg, i) => (
                        <div key={i} className="text-xs text-gray-400">
                          <span
                            className={
                              leg.side === "BUY"
                                ? "text-accent-green"
                                : "text-accent-red"
                            }
                          >
                            {leg.side}
                          </span>{" "}
                          {leg.volume.toFixed(8)} @ {leg.rate.toFixed(8)} on{" "}
                          {leg.exchange}
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
              {(!trades || trades.items.length === 0) && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-gray-500">
                    No trades yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {trades && totalPages > 1 && (
          <div className="flex items-center justify-between text-sm text-gray-400 mt-2">
            <span>{trades.total} trades</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-2 py-1 rounded bg-surface-card border border-gray-600 disabled:opacity-30 hover:bg-surface-hover"
              >
                Prev
              </button>
              <span className="px-2 py-1">
                {page} / {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-2 py-1 rounded bg-surface-card border border-gray-600 disabled:opacity-30 hover:bg-surface-hover"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
