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
    { subject: "VISION_OCR", value: data.vision_confidence * 100 },
    { subject: "LOGIC_R1", value: data.reasoning_confidence * 100 },
    { subject: "VALIDATION", value: data.validation_confidence * 100 },
  ];

  const overall = Math.round(data.overall_confidence * 100);

  return (
    <div className="flex flex-col items-center">
      <div className="h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
            <PolarGrid stroke="#2A2A2A" strokeDasharray="3 3" />
            <PolarAngleAxis 
              dataKey="subject" 
              tick={{ fill: "#6B6B6B", fontSize: 9, fontFamily: "JetBrains Mono, monospace", fontWeight: 700 }} 
            />
            <Radar
              name="Confidence"
              dataKey="value"
              stroke="#ED1C24"
              fill="#ED1C24"
              fillOpacity={0.4}
              dot={{ r: 3, fill: "#ED1C24" }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div className="text-center mt-4 bg-amd-gray-950 px-8 py-3 border border-amd-gray-800 rounded relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-amd-red to-transparent opacity-50" />
        <span className="text-4xl font-black text-white tracking-tighter shadow-[0_0_20px_rgba(237,28,36,0.1)] group-hover:text-amd-red transition-colors duration-500">
          {overall}<span className="text-sm font-mono text-amd-gray-600">%</span>
        </span>
        <p className="text-[9px] font-mono text-amd-gray-500 uppercase tracking-[0.2em] font-black mt-1">
          GLOBAL_CONFIDENCE_SCORE
        </p>
      </div>
    </div>
  );
};
