import { NavLink, Outlet } from "react-router-dom";
import clsx from "clsx";
import { useStatus } from "../api/hooks";
import StatusBadge from "./StatusBadge";
import ExchangeHealth from "./ExchangeHealth";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard" },
  { to: "/opportunities", label: "Opportunities" },
  { to: "/analytics", label: "Analytics" },
  { to: "/trades", label: "Trades" },
  { to: "/settings", label: "Settings" },
];

export default function Layout() {
  const { data: status } = useStatus();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-56 bg-surface-light border-r border-gray-700 flex flex-col shrink-0">
        <div className="p-4 border-b border-gray-700">
          <h1 className="text-xl font-bold text-white tracking-tight">Arby-X</h1>
          <p className="text-xs text-gray-400 mt-1">Arbitrage Dashboard</p>
        </div>

        <nav className="flex-1 p-2 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                clsx(
                  "block px-3 py-2 rounded text-sm transition-colors",
                  isActive
                    ? "bg-accent-blue/20 text-accent-blue font-medium"
                    : "text-gray-300 hover:bg-surface-hover hover:text-white",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {status && (
          <div className="p-3 border-t border-gray-700 text-xs text-gray-400">
            {status.routes.total} routes
          </div>
        )}
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-12 bg-surface-light border-b border-gray-700 flex items-center px-4 gap-4 shrink-0">
          <StatusBadge />
          <div className="flex-1" />
          <ExchangeHealth />
          {status && (
            <span className="text-xs text-gray-400">
              uptime: {formatUptime(status.uptime_seconds)}
            </span>
          )}
        </header>

        <main className="flex-1 p-4 overflow-auto scrollbar-thin">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}
