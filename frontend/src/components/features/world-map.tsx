"use client";

import React, { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from "react-simple-maps";
import { scaleLinear } from "d3-scale";
import { interpolateRgb } from "d3-interpolate";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface CountryData {
  country_code: string;   // ISO 3166-1 alpha-2
  country_name: string;
  participation_pct: number;
  status: "Market Entry" | "Expanding" | "Established";
  influence_score: number;
  audits_completed: number;
  alerts_forenses: number;
  risk_level: "low" | "medium" | "high" | "critical";
}

interface WorldMapProps {
  countries: CountryData[];
  companyName: string;
}

// ── Constants ─────────────────────────────────────────────────────────────────

// Maps world-atlas@2 numeric IDs → ISO alpha-2
// Numeric codes from ISO 3166-1; stored without leading zeros in topojson
const NUM_TO_ISO: Record<string, string> = {
  "484": "MX", "840": "US", "156": "CN",
  "76":  "BR", "076": "BR",
  "826": "GB", "276": "DE", "250": "FR",
  "356": "IN", "724": "ES", "392": "JP",
  "124": "CA",
};

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const STATUS_COLOR: Record<string, string> = {
  "Market Entry": "#33B5E5",
  "Expanding":    "#FFBB33",
  "Established":  "#00C851",
};

const RISK_COLOR: Record<string, string> = {
  low:      "#00C851",
  medium:   "#FFBB33",
  high:     "#FF8800",
  critical: "#ED1C24",
};

// AMD-red heat scale: black → dark-red → AMD red
const heatScale = scaleLinear<string>()
  .domain([0, 15, 35])
  .range(["#0d0d0d", "#6B0000", "#ED1C24"])
  .interpolate(interpolateRgb);

// ── Component ─────────────────────────────────────────────────────────────────

export function WorldMap({ countries, companyName }: WorldMapProps) {
  const [hovered,  setHovered]  = useState<string | null>(null);
  const [selected, setSelected] = useState<CountryData | null>(null);
  const [tooltip,  setTooltip]  = useState({ x: 0, y: 0 });

  // Build lookup by alpha-2 code
  const dataMap = useMemo(() => {
    const m: Record<string, CountryData> = {};
    countries.forEach((c) => { m[c.country_code] = c; });
    return m;
  }, [countries]);

  const onMove = useCallback((e: React.MouseEvent) => {
    setTooltip({ x: e.clientX + 14, y: e.clientY - 8 });
  }, []);

  return (
    <div className="relative w-full h-full flex flex-col" onMouseMove={onMove}>

      {/* Scanline overlay */}
      <div
        className="absolute inset-0 pointer-events-none z-10"
        style={{
          background: "repeating-linear-gradient(transparent 0px, transparent 3px, rgba(237,28,36,0.025) 3px, rgba(237,28,36,0.025) 4px)",
        }}
      />

      {/* HUD corner brackets */}
      {[
        "top-0 left-0 border-t-2 border-l-2",
        "top-0 right-0 border-t-2 border-r-2",
        "bottom-0 left-0 border-b-2 border-l-2",
        "bottom-0 right-0 border-b-2 border-r-2",
      ].map((cls, i) => (
        <div key={i} className={`absolute ${cls} w-6 h-6 border-red-600/60 z-20`} />
      ))}

      {/* Map */}
      <div className="flex-1 relative">
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{ scale: 130, center: [10, 20] }}
          style={{ width: "100%", height: "100%", background: "transparent" }}
        >
          <ZoomableGroup zoom={1} minZoom={0.8} maxZoom={4}>
            <Geographies geography={GEO_URL}>
              {({ geographies }) =>
                geographies.map((geo) => {
                  const numId    = String(geo.id ?? "");
                  const isoCode  = NUM_TO_ISO[numId];
                  const cData    = isoCode ? dataMap[isoCode] : undefined;
                  const isHov    = isoCode === hovered;
                  const isSel    = isoCode === selected?.country_code;
                  const pct      = cData?.participation_pct ?? 0;
                  const fillBase = cData ? heatScale(pct) : "#111111";
                  const fill     = isHov || isSel
                    ? cData ? heatScale(Math.min(pct + 10, 50)) : "#2a2a2a"
                    : fillBase;

                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      onMouseEnter={() => isoCode && setHovered(isoCode)}
                      onMouseLeave={() => setHovered(null)}
                      onClick={() => cData && setSelected(cData === selected ? null : cData)}
                      style={{
                        default: {
                          fill,
                          stroke: isSel ? "#ED1C24" : "#222",
                          strokeWidth: isSel ? 1.5 : 0.4,
                          outline: "none",
                          filter: isSel
                            ? "drop-shadow(0 0 6px #ED1C24)"
                            : isHov && cData
                            ? "drop-shadow(0 0 3px #ED1C2488)"
                            : "none",
                          transition: "fill 0.2s, filter 0.2s",
                        },
                        hover: {
                          fill,
                          stroke: cData ? "#ED1C24" : "#333",
                          strokeWidth: 0.8,
                          outline: "none",
                        },
                        pressed: {
                          fill: "#ED1C24",
                          outline: "none",
                        },
                      }}
                    />
                  );
                })
              }
            </Geographies>
          </ZoomableGroup>
        </ComposableMap>

        {/* Legend */}
        <div className="absolute bottom-3 right-3 bg-black/80 border border-red-900/40 rounded p-3 z-20">
          <div className="text-[8px] font-mono text-red-500/60 uppercase tracking-widest mb-2">
            Market Share
          </div>
          {[
            { label: ">20%", color: "#ED1C24" },
            { label: "10–20%", color: "#8B0000" },
            { label: "5–10%", color: "#4D0000" },
            { label: "<5%",  color: "#1a0000" },
            { label: "N/A",  color: "#111" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2 mb-1">
              <div className="w-3 h-2 rounded-sm border border-white/10" style={{ background: item.color }} />
              <span className="text-[8px] font-mono text-white/40">{item.label}</span>
            </div>
          ))}
        </div>

        {/* Active company label */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
          <motion.div
            key={companyName}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <span className="text-[9px] font-mono text-red-500/70 uppercase tracking-[0.4em]">
              {companyName}
            </span>
          </motion.div>
        </div>
      </div>

      {/* Hover tooltip */}
      <AnimatePresence>
        {hovered && dataMap[hovered] && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="fixed z-50 pointer-events-none bg-black/95 border border-red-900/60 rounded p-3 text-xs shadow-xl"
            style={{ left: tooltip.x, top: tooltip.y, minWidth: 160 }}
          >
            <div className="font-mono font-bold text-white mb-1">{dataMap[hovered].country_name}</div>
            <div
              className="text-xl font-mono font-black mb-1"
              style={{ color: heatScale(dataMap[hovered].participation_pct) }}
            >
              {dataMap[hovered].participation_pct}%
            </div>
            <div className="flex items-center gap-2 mb-1">
              <span
                className="text-[9px] px-1.5 py-0.5 rounded font-mono border"
                style={{
                  color: STATUS_COLOR[dataMap[hovered].status],
                  borderColor: `${STATUS_COLOR[dataMap[hovered].status]}40`,
                  background: `${STATUS_COLOR[dataMap[hovered].status]}15`,
                }}
              >
                {dataMap[hovered].status.toUpperCase()}
              </span>
              <span className="text-[9px] font-mono text-white/40">
                Score {dataMap[hovered].influence_score}/10
              </span>
            </div>
            <div className="text-[9px] font-mono text-white/30">
              Audits: {dataMap[hovered].audits_completed} · Alerts: {dataMap[hovered].alerts_forenses}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Country detail panel */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ x: 280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 280, opacity: 0 }}
            transition={{ type: "spring", damping: 28, stiffness: 220 }}
            className="absolute top-8 right-8 w-56 bg-black/95 border border-red-900/50 rounded-lg p-4 z-30"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-black text-white">{selected.country_name}</span>
              <button
                onClick={() => setSelected(null)}
                className="text-white/30 hover:text-white/70 text-xs"
              >
                ✕
              </button>
            </div>

            <div className="text-3xl font-mono font-black mb-3" style={{ color: heatScale(selected.participation_pct) }}>
              {selected.participation_pct}%
            </div>

            <div className="grid grid-cols-2 gap-2 mb-2">
              {[
                { label: "STATUS",     value: selected.status,           color: STATUS_COLOR[selected.status] },
                { label: "INFLUENCIA", value: `${selected.influence_score}/10`, color: "#fff" },
                { label: "AUDITORÍAS", value: selected.audits_completed.toString(), color: "#fff" },
                { label: "ALERTAS",    value: selected.alerts_forenses.toString(),  color: RISK_COLOR[selected.risk_level] },
              ].map((item) => (
                <div key={item.label} className="bg-black/40 border border-white/5 rounded p-1.5">
                  <div className="text-[8px] font-mono text-white/30 uppercase">{item.label}</div>
                  <div className="text-[10px] font-mono font-bold mt-0.5" style={{ color: item.color }}>
                    {item.value}
                  </div>
                </div>
              ))}
            </div>

            <div className="border border-white/5 rounded p-2">
              <div className="text-[8px] font-mono text-white/30 mb-1.5 uppercase">Risk Level</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min((selected.alerts_forenses / 50) * 100, 100)}%`,
                      background: RISK_COLOR[selected.risk_level],
                    }}
                  />
                </div>
                <span
                  className="text-[9px] font-mono uppercase font-bold"
                  style={{ color: RISK_COLOR[selected.risk_level] }}
                >
                  {selected.risk_level}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
