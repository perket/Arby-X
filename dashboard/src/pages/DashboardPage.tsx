import { useStatus, useOpportunities } from "../api/hooks";
import ComparisonTicker from "../components/ComparisonTicker";
import BalanceCards from "../components/BalanceCard";

export default function DashboardPage() {
  const { data: status } = useStatus();
  const { data: opps } = useOpportunities({ page: 1, per_page: 1 });

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          label="Mode"
          value={status?.mode.toUpperCase() ?? "..."}
          color={status?.mode === "live" ? "text-accent-green" : "text-accent-amber"}
        />
        <StatCard
          label="Routes"
          value={status?.routes.total?.toString() ?? "..."}
        />
        <StatCard
          label="Total Opportunities"
          value={opps?.total?.toString() ?? "..."}
        />
        <StatCard
          label="Uptime"
          value={status ? formatUptime(status.uptime_seconds) : "..."}
        />
      </div>

      {/* Live comparison ticker */}
      <section>
        <h2 className="text-sm font-medium text-gray-400 mb-2 uppercase tracking-wider">
          Live Comparisons
        </h2>
        <ComparisonTicker />
      </section>

      {/* Wallet balances */}
      <section>
        <h2 className="text-sm font-medium text-gray-400 mb-2 uppercase tracking-wider">
          Wallet Balances
        </h2>
        <BalanceCards />
      </section>
    </div>
  );
}

function StatCard({
  label,
  value,
  color = "text-white",
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="bg-surface-card rounded border border-gray-700 p-4">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className={`text-xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}
