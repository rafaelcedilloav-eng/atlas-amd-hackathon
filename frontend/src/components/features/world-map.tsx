"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from "react-simple-maps";
import { scaleLinear } from "d3-scale";

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

export interface CountryData {
  country_code: string;
  country_name: string;
  participation_pct: number;
  status: "Market Entry" | "Expanding" | "Established";
  influence_score: number;
  audits_completed: number;
  alerts_forenses: number;
  risk_level: "low" | "medium" | "high" | "critical";
}

const STATUS_COLORS: Record<string, string> = {
  "Market Entry": "#33B5E5",
  "Expanding": "#FFBB33",
  "Established": "#00C851",
};

const RISK_COLORS: Record<string, string> = {
  low: "#00C851",
  medium: "#FFBB33",
  high: "#FF8800",
  critical: "#ED1C24",
};

const colorScale = scaleLinear<string>()
  .domain([0, 20, 40])
  .range(["#1a1a1a", "#ED1C24", "#FF4444"]);

// world-atlas@2 countries-110m.json uses ISO 3166-1 numeric IDs, not ISO_A2 strings
const NUM_TO_ISO: Record<string, string> = {
  "4":"AF","8":"AL","12":"DZ","24":"AO","32":"AR","36":"AU","40":"AT",
  "50":"BD","56":"BE","68":"BO","76":"BR","100":"BG","116":"KH","120":"CM",
  "124":"CA","152":"CL","156":"CN","170":"CO","188":"CR","191":"HR",
  "192":"CU","203":"CZ","208":"DK","218":"EC","818":"EG","231":"ET",
  "246":"FI","250":"FR","276":"DE","288":"GH","300":"GR","320":"GT",
  "332":"HT","340":"HN","348":"HU","356":"IN","360":"ID","364":"IR",
  "368":"IQ","372":"IE","376":"IL","380":"IT","388":"JM","392":"JP",
  "400":"JO","404":"KE","410":"KR","414":"KW","418":"LA","422":"LB",
  "434":"LY","458":"MY","484":"MX","504":"MA","508":"MZ","524":"NP",
  "528":"NL","554":"NZ","558":"NI","566":"NG","578":"NO","586":"PK",
  "591":"PA","598":"PG","600":"PY","604":"PE","608":"PH","616":"PL",
  "620":"PT","630":"PR","634":"QA","642":"RO","643":"RU","682":"SA",
  "686":"SN","694":"SL","706":"SO","710":"ZA","724":"ES","752":"SE",
  "756":"CH","760":"SY","764":"TH","788":"TN","792":"TR","800":"UG",
  "804":"UA","784":"AE","826":"GB","840":"US","858":"UY","862":"VE",
  "704":"VN","887":"YE","894":"ZM","716":"ZW",
};

export default function WorldMap({ data }: { data?: CountryData[] }) {
  const [selectedCountry, setSelectedCountry] = useState<CountryData | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const activeData = data || [];

  const dataMap = useMemo(() => {
    const map: Record<string, CountryData> = {};
    activeData.forEach((d) => (map[d.country_code] = d));
    return map;
  }, [activeData]);

  const handleMouseMove = (e: React.MouseEvent) => {
    setTooltipPos({ x: e.clientX + 15, y: e.clientY - 10 });
  };

  return (
    <div className="w-full h-full bg-[#0a0a0a] border border-[#333] rounded-lg overflow-hidden flex flex-col min-h-[500px]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#333] flex items-center justify-between bg-black/50">
        <h2 className="text-sm font-mono font-bold text-white tracking-wider">
          GLOBAL INTELLIGENCE // MARKET FOOTPRINT
        </h2>
        <div className="flex items-center gap-4 text-[10px] font-mono">
          <span className="text-[#666]">{activeData.length} JURISDICCIONES</span>
          <span className="text-[#ED1C24]">●</span>
          <span className="text-[#666]">LIVE TELEMETRY</span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Country List */}
        <div className="w-56 border-r border-[#333] overflow-y-auto bg-black/20">
          <div className="p-3 space-y-2">
            {[...activeData].sort((a, b) => b.participation_pct - a.participation_pct).map((country) => (
              <motion.button
                key={country.country_code}
                onClick={() => setSelectedCountry(country)}
                className={`w-full text-left p-2.5 rounded border transition-all ${
                  selectedCountry?.country_code === country.country_code
                    ? "border-[#ED1C24] bg-[#ED1C24]/10"
                    : "border-[#333] bg-[#1a1a1a]/50 hover:border-[#555]"
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-mono text-white font-bold">
                    {country.country_code} {country.country_name}
                  </span>
                  <span
                    className="text-[11px] font-mono font-black"
                    style={{ color: colorScale(country.participation_pct) }}
                  >
                    {country.participation_pct}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold"
                    style={{
                      backgroundColor: `${STATUS_COLORS[country.status]}20`,
                      color: STATUS_COLORS[country.status],
                      border: `1px solid ${STATUS_COLORS[country.status]}40`,
                    }}
                  >
                    {country.status.toUpperCase()}
                  </span>
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Map Container */}
        <div className="flex-1 relative overflow-hidden" onMouseMove={handleMouseMove}>
          <ComposableMap
            projection="geoMercator"
            projectionConfig={{ scale: 140, center: [0, 20] }}
            style={{ width: "100%", height: "100%" }}
          >
            <ZoomableGroup>
              <Geographies geography={GEO_URL}>
                {({ geographies }) =>
                  geographies.map((geo) => {
                    const iso = NUM_TO_ISO[String(geo.id)] ?? null;
                    const countryData = iso ? dataMap[iso] : undefined;

                    return (
                      <Geography
                        key={geo.rsmKey}
                        geography={geo}
                        onMouseEnter={() => iso && setHoveredCountry(iso)}
                        onMouseLeave={() => setHoveredCountry(null)}
                        onClick={() => countryData && setSelectedCountry(countryData)}
                        style={{
                          default: {
                            fill: countryData
                              ? colorScale(countryData.participation_pct)
                              : "#1a1a1a",
                            stroke: "#333",
                            strokeWidth: 0.5,
                            outline: "none",
                          },
                          hover: {
                            fill: countryData
                              ? colorScale(countryData.participation_pct)
                              : "#333",
                            stroke: "#ED1C24",
                            strokeWidth: 1,
                            outline: "none",
                            filter: "brightness(1.3)",
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
          <div className="absolute bottom-4 left-4 bg-[#1a1a1a]/90 border border-[#333] rounded p-3 backdrop-blur-sm">
            <div className="text-[9px] font-mono text-[#666] mb-2 font-bold tracking-widest uppercase">Participation Scale</div>
            <div className="flex items-center gap-1">
              {[0, 10, 20, 30, 40].map((val) => (
                <div key={val} className="flex flex-col items-center">
                  <div className="w-6 h-2" style={{ backgroundColor: colorScale(val) }} />
                  <span className="text-[8px] font-mono text-[#666] mt-1">{val}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tooltip */}
          <AnimatePresence>
            {hoveredCountry && dataMap[hoveredCountry] && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="fixed pointer-events-none z-50 bg-[#0a0a0a] border border-[#ED1C24]/30 rounded p-3 shadow-2xl backdrop-blur-md"
                style={{ left: tooltipPos.x, top: tooltipPos.y }}
              >
                <div className="text-xs font-mono font-black text-white mb-1 uppercase tracking-tighter">
                  {dataMap[hoveredCountry].country_name}
                </div>
                <div className="text-xl font-mono font-black leading-none mb-2" style={{ color: colorScale(dataMap[hoveredCountry].participation_pct) }}>
                  {dataMap[hoveredCountry].participation_pct}%
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                  <span className="text-[9px] text-[#666] font-mono uppercase">Audits:</span>
                  <span className="text-[9px] text-white font-mono font-bold text-right">{dataMap[hoveredCountry].audits_completed}</span>
                  <span className="text-[9px] text-[#666] font-mono uppercase">Risk:</span>
                  <span className="text-[9px] font-mono font-bold text-right uppercase" style={{ color: RISK_COLORS[dataMap[hoveredCountry].risk_level] }}>
                    {dataMap[hoveredCountry].risk_level}
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Detail Panel */}
          <AnimatePresence>
            {selectedCountry && (
              <motion.div
                initial={{ x: 300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 300, opacity: 0 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="absolute top-4 right-4 w-64 bg-[#0a0a0a]/95 border border-[#ED1C24]/50 rounded p-4 shadow-2xl backdrop-blur-xl z-40"
              >
                <div className="flex items-center justify-between mb-4 border-b border-[#333] pb-2">
                  <h3 className="text-xs font-mono font-black text-white uppercase tracking-widest">
                    {selectedCountry.country_name}
                  </h3>
                  <button
                    onClick={() => setSelectedCountry(null)}
                    className="text-[#666] hover:text-white transition-colors"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <div>
                      <div className="text-[9px] text-[#666] font-mono mb-1 tracking-widest uppercase font-bold">Market Share</div>
                      <div className="text-3xl font-mono font-black leading-none" style={{ color: colorScale(selectedCountry.participation_pct) }}>
                        {selectedCountry.participation_pct}%
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[9px] text-[#666] font-mono mb-1 tracking-widest uppercase font-bold">Influence</div>
                      <div className="text-xl font-mono font-black text-white">{selectedCountry.influence_score}<span className="text-[10px] text-[#666]">/10</span></div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-black/40 rounded p-2 border border-[#333]">
                      <div className="text-[9px] text-[#666] font-mono mb-1 font-bold">STATUS</div>
                      <div className="text-[10px] font-mono font-bold uppercase" style={{ color: STATUS_COLORS[selectedCountry.status] }}>
                        {selectedCountry.status}
                      </div>
                    </div>
                    <div className="bg-black/40 rounded p-2 border border-[#333]">
                      <div className="text-[9px] text-[#666] font-mono mb-1 font-bold">AUDITS</div>
                      <div className="text-[10px] font-mono font-black text-white">{selectedCountry.audits_completed}</div>
                    </div>
                  </div>

                  <div className="bg-black/40 rounded p-3 border border-[#333]">
                    <div className="flex justify-between items-center mb-2">
                      <div className="text-[9px] text-[#666] font-mono font-bold tracking-widest">RISK PROFILE</div>
                      <span className="text-[10px] font-mono font-black uppercase" style={{ color: RISK_COLORS[selectedCountry.risk_level] }}>
                        {selectedCountry.risk_level}
                      </span>
                    </div>
                    <div className="h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(selectedCountry.alerts_forenses / 50) * 100}%` }}
                        className="h-full"
                        style={{ backgroundColor: RISK_COLORS[selectedCountry.risk_level] }}
                      />
                    </div>
                    <div className="flex justify-between mt-2">
                      <span className="text-[9px] text-[#666] font-mono">Alertas detectadas:</span>
                      <span className="text-[9px] font-mono font-black text-white">{selectedCountry.alerts_forenses}</span>
                    </div>
                  </div>

                  <button className="w-full py-2 bg-[#ED1C24] text-white font-mono font-black text-[10px] uppercase tracking-widest hover:bg-[#ff1f29] transition-colors rounded">
                    View Forensic Details
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
