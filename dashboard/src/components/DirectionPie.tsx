import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useDirection } from "../api/hooks";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

export default function DirectionPie({ days }: { days: number }) {
  const { data } = useDirection(days);

  if (!data || data.length === 0) {
    return <div className="text-gray-500 text-sm py-8 text-center">No direction data</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="direction"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label={({ direction, percent }) =>
            `${direction} (${(percent * 100).toFixed(0)}%)`
          }
          labelLine={{ stroke: "#6b7280" }}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f2937",
            border: "1px solid #374151",
            borderRadius: 4,
            color: "#e5e7eb",
          }}
        />
        <Legend
          wrapperStyle={{ color: "#9CA3AF", fontSize: 12 }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
