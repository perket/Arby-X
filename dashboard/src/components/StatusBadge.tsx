import { useStatus } from "../api/hooks";

export default function StatusBadge() {
  const { data: status, isLoading } = useStatus();

  if (isLoading || !status) {
    return <span className="text-xs text-gray-500">connecting...</span>;
  }

  const isLive = status.mode === "live";

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
        isLive
          ? "bg-accent-green/20 text-accent-green"
          : "bg-accent-amber/20 text-accent-amber"
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          isLive ? "bg-accent-green animate-pulse" : "bg-accent-amber"
        }`}
      />
      {status.mode}
    </span>
  );
}
