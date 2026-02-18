import { useState } from "react";
import { useConfig, useCurrencyConfig, useCurrencyDiscovery } from "../api/hooks";
import api from "../api/client";

const KEY_LABELS: Record<string, string> = {
  BINANCE_API_KEY: "Binance API Key",
  BINANCE_API_SECRET: "Binance API Secret",
  KRAKEN_API_KEY: "Kraken API Key",
  KRAKEN_API_SECRET: "Kraken API Secret",
};

const ROLE_LABELS: Record<number, string> = {
  0: "Base only",
  1: "Base + Trade",
  2: "Trade (all bases)",
  3: "Trade (BTC only)",
};

function estimateRoles(
  selected: string[],
  commonPairs: [string, string][],
): Record<string, number> {
  const relevant = commonPairs.filter(
    ([b, q]) => selected.includes(b) && selected.includes(q),
  );
  const asQuote = new Set(relevant.map(([, q]) => q));
  const asBase = new Set(relevant.map(([b]) => b));
  const roles: Record<string, number> = {};
  for (const c of selected) {
    const isQ = asQuote.has(c);
    const isB = asBase.has(c);
    if (isQ && isB) roles[c] = 1;
    else if (isQ) roles[c] = 0;
    else if (isB) {
      const bases = relevant.filter(([b]) => b === c).map(([, q]) => q);
      roles[c] = bases.length > 1 ? 2 : 3;
    } else {
      roles[c] = 2;
    }
  }
  return roles;
}

export default function SettingsPage() {
  const { data: config, refetch } = useConfig();
  const { data: currConfig, refetch: refetchCurr } = useCurrencyConfig();
  const [discoverEnabled, setDiscoverEnabled] = useState(false);
  const { data: discovery, isFetching: discovering } =
    useCurrencyDiscovery(discoverEnabled);
  const [selectedCurrencies, setSelectedCurrencies] = useState<string[] | null>(null);
  const [currSaving, setCurrSaving] = useState(false);
  const [currMessage, setCurrMessage] = useState("");
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const handleSave = async () => {
    const updates = Object.fromEntries(
      Object.entries(edits).filter(([, v]) => v.trim()),
    );
    if (Object.keys(updates).length === 0) return;

    setSaving(true);
    setMessage("");
    try {
      const res = await api.put("/api/config", updates);
      setMessage(res.data.message || "Saved");
      setEdits({});
      refetch();
    } catch {
      setMessage("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-lg font-bold text-white">Settings</h1>

      {/* Bot info */}
      {config && (
        <div className="bg-surface-card rounded border border-gray-700 p-4 space-y-2">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-2">
            Bot Info
          </h2>
          <div className="flex gap-6 text-sm">
            <span className="text-gray-400">
              Mode:{" "}
              <span
                className={
                  config.mode === "live" ? "text-accent-green" : "text-accent-amber"
                }
              >
                {config.mode.toUpperCase()}
              </span>
            </span>
            <span className="text-gray-400">
              Routes: <span className="text-white">{config.routes_count}</span>
            </span>
            <span className="text-gray-400">
              Uptime:{" "}
              <span className="text-white">
                {Math.floor(config.uptime_seconds / 3600)}h{" "}
                {Math.floor((config.uptime_seconds % 3600) / 60)}m
              </span>
            </span>
          </div>
        </div>
      )}

      {/* API Keys */}
      <div className="bg-surface-card rounded border border-gray-700 p-4 space-y-4">
        <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
          API Keys
        </h2>
        {config &&
          Object.entries(config.keys).map(([key, masked]) => (
            <div key={key} className="space-y-1">
              <label className="text-xs text-gray-400">{KEY_LABELS[key] ?? key}</label>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    placeholder={masked || "Not set"}
                    value={edits[key] ?? ""}
                    onChange={(e) =>
                      setEdits((prev) => ({ ...prev, [key]: e.target.value }))
                    }
                    className="w-full bg-surface border border-gray-600 rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-accent-blue placeholder:text-gray-600"
                  />
                </div>
              </div>
              <div className="text-xs text-gray-600">Current: {masked}</div>
            </div>
          ))}

        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={handleSave}
            disabled={saving || Object.values(edits).every((v) => !v.trim())}
            className="px-4 py-2 bg-accent-blue text-white rounded text-sm font-medium hover:bg-accent-blue/80 disabled:opacity-30 transition-colors"
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
          {message && (
            <span className="text-sm text-accent-amber">{message}</span>
          )}
        </div>
      </div>
      {/* Currency Selection */}
      <div className="bg-surface-card rounded border border-gray-700 p-4 space-y-4">
        <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
          Currency Selection
        </h2>

        {/* Current config */}
        {currConfig && (
          <div className="space-y-2">
            <div className="text-sm text-gray-300">
              <span className="text-gray-400">Active currencies: </span>
              {currConfig.selected.map((c) => (
                <span
                  key={c}
                  className="inline-block bg-surface border border-gray-600 rounded px-2 py-0.5 text-xs mr-1 mb-1"
                >
                  {c}{" "}
                  <span className="text-gray-500">
                    ({ROLE_LABELS[currConfig.roles[c]] ?? "?"})
                  </span>
                </span>
              ))}
            </div>
            <div className="text-xs text-gray-500">
              {Object.keys(currConfig.markets).length} markets generated
            </div>
          </div>
        )}

        {/* Discover button */}
        <button
          onClick={() => setDiscoverEnabled(true)}
          disabled={discovering}
          className="px-4 py-2 bg-gray-700 text-white rounded text-sm font-medium hover:bg-gray-600 disabled:opacity-30 transition-colors"
        >
          {discovering ? "Discovering..." : "Discover Available"}
        </button>

        {/* Checkbox grid */}
        {discovery && (
          <div className="space-y-3">
            <div className="text-xs text-gray-400">
              {discovery.available_currencies.length} currencies found on both
              exchanges. Select which to monitor:
            </div>
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2 max-h-64 overflow-y-auto">
              {discovery.available_currencies.map((c) => {
                const active = selectedCurrencies ?? discovery.selected_currencies;
                const checked = active.includes(c);
                return (
                  <label
                    key={c}
                    className={`flex items-center gap-1.5 text-sm px-2 py-1 rounded cursor-pointer ${
                      checked
                        ? "bg-accent-blue/20 text-white"
                        : "text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => {
                        const prev = selectedCurrencies ?? [
                          ...discovery.selected_currencies,
                        ];
                        setSelectedCurrencies(
                          checked
                            ? prev.filter((x) => x !== c)
                            : [...prev, c].sort(),
                        );
                      }}
                      className="accent-accent-blue"
                    />
                    {c}
                  </label>
                );
              })}
            </div>

            {/* Preview */}
            {selectedCurrencies && selectedCurrencies.length > 0 && (
              <div className="bg-surface rounded border border-gray-600 p-3 space-y-1">
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">
                  Role Preview
                </div>
                {Object.entries(
                  estimateRoles(selectedCurrencies, discovery.common_pairs),
                ).map(([c, role]) => (
                  <div key={c} className="text-sm text-gray-300">
                    <span className="text-white font-mono w-8 inline-block">
                      {c}
                    </span>{" "}
                    <span className="text-gray-500">
                      {ROLE_LABELS[role] ?? `role ${role}`}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Save */}
            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={async () => {
                  const toSave = selectedCurrencies ?? discovery.selected_currencies;
                  if (toSave.length === 0) return;
                  setCurrSaving(true);
                  setCurrMessage("");
                  try {
                    const res = await api.put("/api/currencies", {
                      currencies: toSave,
                    });
                    setCurrMessage(res.data.message || "Saved");
                    setSelectedCurrencies(null);
                    refetchCurr();
                  } catch {
                    setCurrMessage("Failed to save");
                  } finally {
                    setCurrSaving(false);
                  }
                }}
                disabled={
                  currSaving ||
                  !selectedCurrencies ||
                  selectedCurrencies.length === 0
                }
                className="px-4 py-2 bg-accent-blue text-white rounded text-sm font-medium hover:bg-accent-blue/80 disabled:opacity-30 transition-colors"
              >
                {currSaving ? "Saving..." : "Save Currencies"}
              </button>
              {currMessage && (
                <span className="text-sm text-accent-amber">{currMessage}</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
