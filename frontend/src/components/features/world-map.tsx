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

// Actualizamos la interfaz para coincidir con el contrato MarketData
export interface CountryData {
  country_code: string; // ISO 3166-1 Alpha-2
  country_name: string;
  participation_pct: number;
  status: "Market Entry" | "Expanding" | "Established";
  influence_score: number;
  audits_completed: number;
  alerts_forenses: number;
  risk_level: "low" | "medium" | "high" | "critical";
}

// Mapeo de estados a colores
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

// Escala para participación
const colorScale = scaleLinear<string>()
  .domain([0, 20, 40])
  .range(["#1a1a1a", "#ED1C24", "#FF4444"]);

// Mapeo inverso de ISO a numérico para búsquedas eficientes
const ISO_TO_NUM: Record<string, string> = {
  "AF":"4","AL":"8","DZ":"12","AO":"24","AR":"32","AU":"36","AT":"40",
  "BD":"50","BE":"56","BO":"68","BR":"76","BG":"100","KH":"116","CM":"120",
  "CA":"124","CL":"152","CN":"156","CO":"170","CR":"188","HR":"191",
  "CU":"192","CZ":"203","DK":"208","EC":"218","EG":"818","ET":"231",
  "FI":"246","FR":"250","DE":"276","GH":"288","GR":"300","GT":"320",
  "HT":"332","HN":"340","HU":"348","IN":"356","ID":"360","IR":"364",
  "IQ":"368","IE":"372","IL":"376","IT":"380","JM":"388","JP":"392",
  "JO":"400","KE":"404","KR":"410","KW":"414","LA":"418","LB":"422",
  "LY":"434","MY":"458","MX":"484","MA":"504","MZ":"508","NP":"524",
  "NL":"528","NZ":"554","NI":"558","NG":"566","NO":"578","PK":"586",
  "PA":"591","PG":"598","PY":"600","PE":"604","PH":"608","PL":"616",
  "PT":"620","PR":"630","QA":"634","RO":"642","RU":"643","SA":"682",
  "SN":"686","SL":"694","SO":"706","ZA":"710","ES":"724","SE":"752",
  "CH":"756","SY":"760","TH":"764","TN":"788","TR":"792","UG":"800",
  "UA":"804","AE":"784","GB":"826","US":"840","UY":"858","VE":"862",
  "VN":"704","YE":"887","ZM":"894","ZW":"716"
};

export default function WorldMap({ data }: { data?: CountryData[] }) {
  const [selectedCountry, setSelectedCountry] = useState<CountryData | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const activeData = data || [];

  // Optimizamos el mapeo de datos usando useMemo
  const dataMap = useMemo(() => {
    const map: Record<string, CountryData> = {};
    activeData.forEach((d) => {
      if (d.country_code && d.country_code.length === 2) {
        map[d.country_code.toUpperCase()] = d;
      }
    });
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
            {[...activeData]
              .sort((a, b) => b.participation_pct - a.participation_pct)
              .map((country) => (
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
                    // Convertimos el ID numérico a código ISO
                    const isoCode = ISO_TO_NUM[geo.properties.ISO_A2] 
                      ? geo.properties.ISO_A2 
                      : Object.keys(ISO_TO_NUM).find(key => ISO_TO_NUM[key] === String(geo.id));
                    
                    // Obtenemos los datos del país si existen
                    const countryData = isoCode ? dataMap[isoCode.toUpperCase()] : undefined;

                    return (
                      <Geography
                        key={geo.rsmKey}
                        geography={geo}
                        onMouseEnter={() => isoCode && setHoveredCountry(isoCode.toUpperCase())}
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
