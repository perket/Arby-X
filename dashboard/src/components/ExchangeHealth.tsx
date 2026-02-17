import { useStatus } from "../api/hooks";

export default function ExchangeHealth() {
  const { data: status } = useStatus();

  if (!status) return null;

  return (
    <div className="flex items-center gap-3">
      {Object.entries(status.exchange_health).map(([name, health]) => (
        <div key={name} className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              health === "connected" ? "bg-accent-green" : "bg-accent-red"
            }`}
          />
          <span className="text-xs text-gray-300 capitalize">{name}</span>
        </div>
      ))}
    </div>
  );
}
