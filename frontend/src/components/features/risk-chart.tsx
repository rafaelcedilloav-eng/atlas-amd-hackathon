"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

interface RiskChartProps {
  distribution: Record<string, number>;
}

const COLOR_MAP: Record<string, string> = {
  FRAUDE_CONFIRMADO: "#ef4444",
  SOSPECHOSO: "#f97316",
  LIMPIO: "#10b981",
  UNKNOWN: "#6b7280",
};

const LABEL_MAP: Record<string, string> = {
  FRAUDE_CONFIRMADO: "Fraude Confirmado",
  SOSPECHOSO: "Sospechoso",
  LIMPIO: "Limpio",
  UNKNOWN: "Sin clasificar",
};

export function RiskChart({ distribution }: RiskChartProps) {
  const data = Object.entries(distribution).map(([key, value]) => ({
    name: LABEL_MAP[key] ?? key,
    value,
    color: COLOR_MAP[key] ?? "#6b7280",
  }));

  if (data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-white/20 italic text-sm">Sin auditorías aún</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={4}
          dataKey="value"
          strokeWidth={0}
        >
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.color} opacity={0.9} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "12px",
            color: "white",
            fontSize: "12px",
          }}
          formatter={(value: number, name: string) => [value, name]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => (
            <span style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px" }}>
              {value}
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
