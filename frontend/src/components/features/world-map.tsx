"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as THREE from "three";
import { scaleLinear } from "d3-scale";

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";
void GEO_URL; // kept for future GeoJSON-based point cloud (Phase 2)

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
  low: "#00D966",
  medium: "#FFB800",
  high: "#FF8800",
  critical: "#ED1C24",
};

const colorScale = scaleLinear<string>()
  .domain([0, 20, 40])
  .range(["#1a1a1a", "#ED1C24", "#FF4444"]);

const COUNTRY_COORDS: Record<string, [number, number]> = {
  "MX": [23.6345, -102.5528],
  "US": [37.0902, -95.7129],
  "CN": [35.8617, 104.1954],
  "BR": [-14.2350, -51.9253],
  "GB": [55.3781, -3.4360],
  "DE": [51.1657, 10.4515],
  "FR": [46.2276, 2.2137],
  "IN": [20.5937, 78.9629],
  "ES": [40.4637, -3.7492],
  "JP": [36.2048, 138.2529],
  "CA": [56.1304, -106.3468],
  "AU": [-25.2744, 133.7751],
  "RU": [61.5240, 105.3188],
  "AR": [-38.4161, -63.6167],
  "IT": [41.8719, 12.5674],
  "KR": [35.9078, 127.7669],
  "TR": [38.9637, 35.2433],
  "SA": [23.8859, 45.0792],
  "ZA": [-30.5595, 22.9375],
  "NG": [9.0820, 8.6753],
};

function latLngToVector3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

export default function WorldMap({ data }: { data?: CountryData[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const threeRef = useRef<{
    renderer?: THREE.WebGLRenderer;
    scene?: THREE.Scene;
    camera?: THREE.PerspectiveCamera;
    globeGroup?: THREE.Group;
    animId?: number;
    pillars: { mesh: THREE.Mesh; code: string }[];
  }>({ pillars: [] });

  const [selectedCountry, setSelectedCountry] = useState<CountryData | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const activeData = data || [];
  const dataMap = useMemo(() => {
    const map: Record<string, CountryData> = {};
    activeData.forEach((d) => { map[d.country_code.toUpperCase()] = d; });
    return map;
  }, [activeData]);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvasContainer = canvasRef.current;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      45,
      canvasContainer.clientWidth / canvasContainer.clientHeight,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(canvasContainer.clientWidth, canvasContainer.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    canvasContainer.appendChild(renderer.domElement);

    const globeGroup = new THREE.Group();
    scene.add(globeGroup);
    threeRef.current = { renderer, scene, camera, globeGroup, pillars: [] };

    // 1. Fibonacci sphere point cloud
    const pointsGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(8000 * 3);
    for (let i = 0; i < 8000; i++) {
      const phi = Math.acos(-1 + (2 * i) / 8000);
      const theta = Math.sqrt(8000 * Math.PI) * phi;
      positions[i * 3]     = 2 * Math.cos(theta) * Math.sin(phi);
      positions[i * 3 + 1] = 2 * Math.sin(theta) * Math.sin(phi);
      positions[i * 3 + 2] = 2 * Math.cos(phi);
    }
    pointsGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    globeGroup.add(new THREE.Points(
      pointsGeo,
      new THREE.PointsMaterial({ color: 0x00d4ff, size: 0.015, transparent: true, opacity: 0.6 })
    ));

    // 2. Risk pillars
    activeData.forEach((country) => {
      const coords = COUNTRY_COORDS[country.country_code];
      if (!coords) return;

      const height = (country.participation_pct / 100) * 1.5 + 0.1;
      const geo = new THREE.BoxGeometry(0.04, height, 0.04);
      geo.translate(0, height / 2, 0); // pivot at base

      const color = RISK_COLORS[country.risk_level] || "#00D4FF";
      const mat = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.2,
        transparent: true,
        opacity: 0.9,
      });

      const pillar = new THREE.Mesh(geo, mat);
      pillar.position.copy(latLngToVector3(coords[0], coords[1], 2));
      pillar.lookAt(new THREE.Vector3(0, 0, 0));
      pillar.rotateX(Math.PI / 2);

      globeGroup.add(pillar);
      threeRef.current.pillars.push({ mesh: pillar, code: country.country_code });
    });

    // 3. Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.3));
    const pl = new THREE.PointLight(0xffffff, 1);
    pl.position.set(10, 10, 10);
    scene.add(pl);

    camera.position.z = 6;

    // 4. Mouse interaction
    let isDragging = false;
    let previousMouseX = 0;
    let previousMouseY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      previousMouseX = e.clientX;
      previousMouseY = e.clientY;
    };
    const onMouseUp = () => { isDragging = false; };

    const onMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const deltaX = e.clientX - previousMouseX;
        const deltaY = e.clientY - previousMouseY;
        globeGroup.rotation.y += deltaX * 0.005;
        globeGroup.rotation.x += deltaY * 0.005;
        previousMouseX = e.clientX;
        previousMouseY = e.clientY;
        return;
      }

      // Hover via raycasting
      const rect = renderer.domElement.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(new THREE.Vector2(nx, ny), camera);
      const meshes = threeRef.current.pillars.map((p) => p.mesh);
      const intersects = raycaster.intersectObjects(meshes);

      // Reset all emissive intensities first
      threeRef.current.pillars.forEach(
        (p) => ((p.mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.2)
      );

      if (intersects.length > 0) {
        const hit = threeRef.current.pillars.find((p) => p.mesh === intersects[0].object);
        if (hit) {
          (hit.mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = 1.0;
          setHoveredCountry(hit.code);
          setTooltipPos({ x: e.clientX + 15, y: e.clientY - 10 });
        }
      } else {
        setHoveredCountry(null);
      }
    };

    const onClick = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(new THREE.Vector2(nx, ny), camera);
      const intersects = raycaster.intersectObjects(threeRef.current.pillars.map((p) => p.mesh));
      if (intersects.length > 0) {
        const hit = threeRef.current.pillars.find((p) => p.mesh === intersects[0].object);
        if (hit) setSelectedCountry(dataMap[hit.code] || null);
      }
    };

    canvasContainer.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mouseup", onMouseUp);
    canvasContainer.addEventListener("mousemove", onMouseMove);
    canvasContainer.addEventListener("click", onClick);

    // 5. Animation loop
    let animId = 0;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      if (!isDragging) globeGroup.rotation.y += 0.001;
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      if (!canvasRef.current) return;
      camera.aspect = canvasRef.current.clientWidth / canvasRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(canvasRef.current.clientWidth, canvasRef.current.clientHeight);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
      pointsGeo.dispose();
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("resize", onResize);
      canvasContainer.removeEventListener("mousedown", onMouseDown);
      canvasContainer.removeEventListener("mousemove", onMouseMove);
      canvasContainer.removeEventListener("click", onClick);
      // Fix: remove canvas so re-runs don't stack renderers
      if (canvasContainer.contains(renderer.domElement)) {
        canvasContainer.removeChild(renderer.domElement);
      }
    };
  }, [activeData, dataMap]);

  return (
    <div className="w-full h-full bg-[#0a0a0a] border border-[#333] rounded-lg overflow-hidden flex flex-col min-h-[500px]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#333] flex items-center justify-between bg-black/50 z-10">
        <h2 className="text-sm font-mono font-bold text-white tracking-wider">
          GLOBAL INTELLIGENCE // FORENSIC GLOBE 3D
        </h2>
        <div className="flex items-center gap-4 text-[10px] font-mono">
          <span className="text-[#666]">{activeData.length} JURISDICCIONES</span>
          <span className="text-[#ED1C24]">●</span>
          <span className="text-[#666]">LIVE TELEMETRY</span>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden relative" ref={containerRef}>
        {/* Country List */}
        <div className="w-56 border-r border-[#333] overflow-y-auto bg-black/20 z-10">
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

        {/* 3D Globe */}
        <div ref={canvasRef} className="flex-1 relative cursor-grab active:cursor-grabbing" />

        {/* Legend */}
        <div className="absolute bottom-4 left-60 bg-[#1a1a1a]/90 border border-[#333] rounded p-3 backdrop-blur-sm z-10 pointer-events-none">
          <div className="text-[9px] font-mono text-[#666] mb-2 font-bold tracking-widest uppercase">Risk Severity</div>
          <div className="flex gap-3">
            {Object.entries(RISK_COLORS).map(([lvl, col]) => (
              <div key={lvl} className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: col }} />
                <span className="text-[8px] font-mono text-[#666] uppercase">{lvl}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Tooltip */}
        <AnimatePresence>
          {hoveredCountry && dataMap[hoveredCountry] && (
            <motion.div
              key={hoveredCountry}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="fixed pointer-events-none z-50 bg-[#0a0a0a] border border-[#ED1C24]/30 rounded p-3 shadow-2xl backdrop-blur-md"
              style={{ left: tooltipPos.x, top: tooltipPos.y }}
            >
              <div className="text-xs font-mono font-black text-white mb-1 uppercase tracking-tighter">
                {dataMap[hoveredCountry].country_name}
              </div>
              <div className="text-lg font-mono font-black text-[#00D4FF]">
                {dataMap[hoveredCountry].participation_pct}% Participation
              </div>
              <div className="text-[9px] font-mono mt-1 uppercase font-bold" style={{ color: RISK_COLORS[dataMap[hoveredCountry].risk_level] }}>
                {dataMap[hoveredCountry].risk_level} RISK
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
                <button onClick={() => setSelectedCountry(null)} className="text-[#666] hover:text-white transition-colors">✕</button>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <div>
                    <div className="text-[9px] text-[#666] font-mono mb-1 tracking-widest uppercase font-bold">Market Share</div>
                    <div className="text-3xl font-mono font-black leading-none" style={{ color: RISK_COLORS[selectedCountry.risk_level] }}>
                      {selectedCountry.participation_pct}%
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[9px] text-[#666] font-mono mb-1 tracking-widest uppercase font-bold">Influence</div>
                    <div className="text-xl font-mono font-black text-white">
                      {selectedCountry.influence_score}<span className="text-[10px] text-[#666]">/10</span>
                    </div>
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
                      animate={{ width: `${Math.min(100, (selectedCountry.alerts_forenses / 50) * 100)}%` }}
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
  );
}
