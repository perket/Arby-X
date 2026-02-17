import { useReturns } from "../api/hooks";

export default function ReturnProjections() {
  const { data } = useReturns();

  if (!data) return null;

  const cards = [
    { label: "Daily", value: data.daily, pct: true },
    { label: "Weekly", value: data.weekly, pct: true },
    { label: "Monthly", value: data.monthly, pct: true },
    { label: "Yearly", value: data.yearly, pct: true },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {cards.map((c) => (
          <div key={c.label} className="bg-surface-card rounded border border-gray-700 p-4">
            <div className="text-xs text-gray-400 mb-1">{c.label} Return</div>
            <div className="text-lg font-bold text-accent-green tabular-nums">
              {(c.value * 100).toFixed(4)}%
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-6 text-xs text-gray-400">
        <span>Avg spread: {data.avg_spread_pct.toFixed(4)}%</span>
        <span>Total trades: {data.total_trades}</span>
        <span>Over {data.span_days} days</span>
      </div>
    </div>
  );
}
