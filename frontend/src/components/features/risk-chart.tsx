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
  FRAUDE_CONFIRMADO: "#ED1C24", // AMD Red
  SOSPECHOSO: "#FFB300",         // Accent Warning
  LIMPIO: "#00E676",             // Accent Success
  UNKNOWN: "#2A2A2A",            // Technical Gray
};

const LABEL_MAP: Record<string, string> = {
  FRAUDE_CONFIRMADO: "CONFIRMED_FRAUD",
  SOSPECHOSO: "SUSPICIOUS",
  LIMPIO: "VERIFIED_CLEAN",
  UNKNOWN: "UNCLASSIFIED",
};

export function RiskChart({ distribution }: RiskChartProps) {
  const data = Object.entries(distribution).map(([key, value]) => ({
    name: LABEL_MAP[key] ?? key,
    value,
    color: COLOR_MAP[key] ?? "#2A2A2A",
  }));

  if (data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-amd-gray-600 font-mono text-[10px] uppercase tracking-widest">Awaiting_Telemetry_Data</p>
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
          innerRadius={65}
          outerRadius={95}
          paddingAngle={5}
          dataKey="value"
          strokeWidth={0}
        >
          {data.map((entry, index) => (
            <Cell 
              key={index} 
              fill={entry.color} 
              style={{ filter: `drop-shadow(0 0 8px ${entry.color}40)` }}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "#0A0A0A",
            border: "1px solid #1A1A1A",
            borderRadius: "0px",
            color: "white",
            fontSize: "10px",
            fontFamily: "JetBrains Mono, monospace",
            textTransform: "uppercase",
            boxShadow: "0 10px 20px rgba(0,0,0,0.5)"
          }}
          itemStyle={{ color: "white" }}
          cursor={{ fill: "transparent" }}
        />
        <Legend
          verticalAlign="bottom"
          iconType="rect"
          iconSize={8}
          formatter={(value) => (
            <span className="text-amd-gray-500 font-mono text-[9px] uppercase tracking-tighter ml-1">
              {value}
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
