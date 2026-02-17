import { useState } from "react";
import clsx from "clsx";
import { useOpportunities } from "../api/hooks";
import { format } from "date-fns";

export default function OpportunityTable() {
  const [page, setPage] = useState(1);
  const [routeLabel, setRouteLabel] = useState("");
  const [minSpread, setMinSpread] = useState("");
  const [executed, setExecuted] = useState<string>("");
  const [routeType, setRouteType] = useState("");
  const [search, setSearch] = useState("");
  const [sortField, setSortField] = useState<string>("ts");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const { data, isLoading } = useOpportunities({
    page,
    per_page: 50,
    route_label: routeLabel || undefined,
    min_spread: minSpread ? parseFloat(minSpread) : undefined,
    executed: executed === "" ? undefined : executed === "true",
    route_type: routeType || undefined,
    search: search || undefined,
  });

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const items = data?.items ?? [];
  const sorted = [...items].sort((a, b) => {
    const av = a[sortField as keyof typeof a];
    const bv = b[sortField as keyof typeof b];
    if (av == null || bv == null) return 0;
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return sortDir === "asc" ? cmp : -cmp;
  });

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 1;

  return (
    <div className="space-y-3">
      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-end">
        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="bg-surface-card border border-gray-600 rounded px-2 py-1 text-sm text-gray-200 w-40 focus:outline-none focus:border-accent-blue"
        />
        <input
          type="text"
          placeholder="Route label"
          value={routeLabel}
          onChange={(e) => { setRouteLabel(e.target.value); setPage(1); }}
          className="bg-surface-card border border-gray-600 rounded px-2 py-1 text-sm text-gray-200 w-32 focus:outline-none focus:border-accent-blue"
        />
        <input
          type="number"
          step="0.01"
          placeholder="Min spread %"
          value={minSpread}
          onChange={(e) => { setMinSpread(e.target.value); setPage(1); }}
          className="bg-surface-card border border-gray-600 rounded px-2 py-1 text-sm text-gray-200 w-28 focus:outline-none focus:border-accent-blue"
        />
        <select
          value={executed}
          onChange={(e) => { setExecuted(e.target.value); setPage(1); }}
          className="bg-surface-card border border-gray-600 rounded px-2 py-1 text-sm text-gray-200 focus:outline-none focus:border-accent-blue"
        >
          <option value="">All</option>
          <option value="true">Executed</option>
          <option value="false">Not executed</option>
        </select>
        <select
          value={routeType}
          onChange={(e) => { setRouteType(e.target.value); setPage(1); }}
          className="bg-surface-card border border-gray-600 rounded px-2 py-1 text-sm text-gray-200 focus:outline-none focus:border-accent-blue"
        >
          <option value="">All types</option>
          <option value="direct">Direct</option>
          <option value="multi_leg">Multi-leg</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400 text-xs">
              {[
                { key: "ts", label: "Time" },
                { key: "route_label", label: "Route" },
                { key: "route_type", label: "Type" },
                { key: "spread_pct", label: "Spread %" },
                { key: "buy_exchange", label: "Direction" },
                { key: "buy_rate", label: "Buy Rate" },
                { key: "sell_rate", label: "Sell Rate" },
                { key: "executed", label: "Exec" },
              ].map((col) => (
                <th
                  key={col.key}
                  className="text-left py-2 px-2 cursor-pointer hover:text-white select-none"
                  onClick={() => toggleSort(col.key)}
                >
                  {col.label}
                  {sortField === col.key && (sortDir === "asc" ? " ↑" : " ↓")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={8} className="py-8 text-center text-gray-500">
                  Loading...
                </td>
              </tr>
            )}
            {!isLoading && sorted.length === 0 && (
              <tr>
                <td colSpan={8} className="py-8 text-center text-gray-500">
                  No opportunities found
                </td>
              </tr>
            )}
            {sorted.map((opp) => (
              <tr
                key={opp.id}
                className="border-b border-gray-800 hover:bg-surface-hover transition-colors"
              >
                <td className="py-1.5 px-2 text-gray-300 tabular-nums whitespace-nowrap">
                  {format(new Date(opp.ts), "MM-dd HH:mm:ss")}
                </td>
                <td className="py-1.5 px-2 text-white font-medium">{opp.route_label}</td>
                <td className="py-1.5 px-2">
                  <span
                    className={clsx(
                      "text-xs px-1.5 py-0.5 rounded",
                      opp.route_type === "direct"
                        ? "bg-accent-blue/20 text-accent-blue"
                        : "bg-accent-purple/20 text-accent-purple",
                    )}
                  >
                    {opp.route_type === "direct" ? "Direct" : "Multi-leg"}
                  </span>
                </td>
                <td
                  className={clsx(
                    "py-1.5 px-2 font-medium tabular-nums",
                    opp.spread_pct > 0.8
                      ? "text-accent-green"
                      : opp.spread_pct > 0.5
                        ? "text-accent-amber"
                        : "text-gray-300",
                  )}
                >
                  {opp.spread_pct.toFixed(4)}%
                </td>
                <td className="py-1.5 px-2 text-gray-300 text-xs">
                  {opp.buy_exchange} &rarr; {opp.sell_exchange}
                </td>
                <td className="py-1.5 px-2 text-gray-300 tabular-nums">
                  {opp.buy_rate.toFixed(8)}
                </td>
                <td className="py-1.5 px-2 text-gray-300 tabular-nums">
                  {opp.sell_rate.toFixed(8)}
                </td>
                <td className="py-1.5 px-2">
                  {opp.executed ? (
                    <span className="text-accent-green text-xs">Yes</span>
                  ) : (
                    <span className="text-gray-500 text-xs">No</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-400">
          <span>
            {data.total} opportunities
          </span>
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
    </div>
  );
}
