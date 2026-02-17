import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useFrequency } from "../api/hooks";

export default function SpreadChart({ days }: { days: number }) {
  const { data } = useFrequency(days);

  if (!data || data.length === 0) {
    return <div className="text-gray-500 text-sm py-8 text-center">No frequency data</div>;
  }

  const chartData = data.map((d) => ({
    hour: d.hour.slice(5, 16),
    count: d.count,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="hour"
          tick={{ fill: "#9CA3AF", fontSize: 10 }}
          interval="preserveStartEnd"
        />
        <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f2937",
            border: "1px solid #374151",
            borderRadius: 4,
            color: "#e5e7eb",
          }}
        />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
