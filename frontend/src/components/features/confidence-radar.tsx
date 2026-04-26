"use client";

import { ConfidenceBreakdown } from "@/types/atlas";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

interface ConfidenceRadarProps {
  data: ConfidenceBreakdown;
}

export const ConfidenceRadar = ({ data }: ConfidenceRadarProps) => {
  const chartData = [
    { subject: "Visión", value: data.vision_confidence * 100 },
    { subject: "Razonamiento", value: data.reasoning_confidence * 100 },
    { subject: "Validación", value: data.validation_confidence * 100 },
  ];

  const overall = Math.round(data.overall_confidence * 100);

  return (
    <div className="flex flex-col items-center">
      <div className="h-[200px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
            <PolarGrid stroke="#ffffff20" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: "#ffffff60", fontSize: 10 }} />
            <Radar
              name="Confianza"
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.5}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div className="text-center mt-2">
        <span className="text-3xl font-black text-white">{overall}%</span>
        <p className="text-[10px] text-white/40 uppercase tracking-widest font-bold">
          Confianza Global
        </p>
      </div>
    </div>
  );
};
