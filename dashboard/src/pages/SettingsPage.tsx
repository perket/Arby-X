import { useState } from "react";
import { useConfig } from "../api/hooks";
import api from "../api/client";

const KEY_LABELS: Record<string, string> = {
  BINANCE_API_KEY: "Binance API Key",
  BINANCE_API_SECRET: "Binance API Secret",
  KRAKEN_API_KEY: "Kraken API Key",
  KRAKEN_API_SECRET: "Kraken API Secret",
};

export default function SettingsPage() {
  const { data: config, refetch } = useConfig();
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
    </div>
  );
}
