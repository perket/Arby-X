import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useTopPairs } from "../api/hooks";

export default function PairBarChart({ days }: { days: number }) {
  const { data } = useTopPairs(days);

  if (!data || data.length === 0) {
    return <div className="text-gray-500 text-sm py-8 text-center">No pair data</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 60 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis type="number" tick={{ fill: "#9CA3AF", fontSize: 11 }} />
        <YAxis
          type="category"
          dataKey="route_label"
          tick={{ fill: "#e5e7eb", fontSize: 11 }}
          width={80}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f2937",
            border: "1px solid #374151",
            borderRadius: 4,
            color: "#e5e7eb",
          }}
        />
        <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
