import { useWallets } from "../api/hooks";

export default function BalanceCards() {
  const { data } = useWallets();

  if (!data) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {Object.entries(data).map(([exchange, currencies]) => (
        <div key={exchange} className="bg-surface-card rounded border border-gray-700 p-4">
          <h3 className="text-sm font-medium text-gray-300 capitalize mb-3">{exchange}</h3>
          <div className="space-y-2">
            {Object.entries(currencies)
              .filter(([, bal]) => bal.total > 0)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([currency, bal]) => (
                <div key={currency} className="flex justify-between items-center">
                  <span className="text-sm text-white font-medium">{currency}</span>
                  <div className="text-right">
                    <span className="text-sm text-gray-200 tabular-nums">
                      {bal.total.toFixed(8)}
                    </span>
                    {bal.reserved > 0 && (
                      <span className="text-xs text-gray-500 ml-1">
                        ({bal.reserved.toFixed(4)} reserved)
                      </span>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
