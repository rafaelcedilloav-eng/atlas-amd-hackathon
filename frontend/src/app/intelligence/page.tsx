"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import dynamic from "next/dynamic";
import * as THREE from "three";
import { motion, AnimatePresence } from "framer-motion";
import type { CountryData } from "@/components/features/world-map";

// Dynamic import — react-simple-maps is client-only (no SSR)
const WorldMap = dynamic(
  () => import("@/components/features/world-map").then((m) => m.default),
  { ssr: false, loading: () => <MapPlaceholder /> }
);

// ── Nav ───────────────────────────────────────────────────────────────────────

const NAV_LINKS = [
  { href: "/dashboard",    label: "Dashboard_Overview"  },
  { href: "/audits",       label: "Forensic_Archive"    },
  { href: "/analytics",    label: "Analytics_Vault"     },
  { href: "/hardware",     label: "Orchestration_Node"  },
  { href: "/intelligence", label: "Global_Intelligence" },
];

// ── Demo data ─────────────────────────────────────────────────────────────────

interface Company {
  id: string;
  name: string;
  sector: string;
  affiliates: { id: string; name: string; role: string }[];
  countries: CountryData[];
}

const COMPANIES: Company[] = [
  {
    id: "nexus",
    name: "Nexus Global Logistics",
    sector: "Logistics",
    affiliates: [
      { id: "nexus-air",      name: "Nexus Air Cargo",           role: "Air Freight" },
      { id: "nexus-maritime", name: "Nexus Maritime Solutions",  role: "Sea Freight" },
      { id: "nexus-customs",  name: "Nexus Customs Brokerage",   role: "Customs" },
    ],
    countries: [
      { country_code: "MX", country_name: "México",         participation_pct: 35.5, status: "Established",  influence_score: 8, audits_completed: 128, alerts_forenses: 23, risk_level: "medium" },
      { country_code: "US", country_name: "Estados Unidos", participation_pct: 28.0, status: "Established",  influence_score: 9, audits_completed: 245, alerts_forenses: 18, risk_level: "low"    },
      { country_code: "CN", country_name: "China",          participation_pct: 15.0, status: "Expanding",    influence_score: 7, audits_completed: 89,  alerts_forenses: 45, risk_level: "high"   },
      { country_code: "BR", country_name: "Brasil",         participation_pct: 8.5,  status: "Expanding",    influence_score: 6, audits_completed: 67,  alerts_forenses: 12, risk_level: "medium" },
      { country_code: "GB", country_name: "Reino Unido",    participation_pct: 5.0,  status: "Market Entry", influence_score: 5, audits_completed: 34,  alerts_forenses: 3,  risk_level: "low"    },
      { country_code: "DE", country_name: "Alemania",       participation_pct: 3.5,  status: "Market Entry", influence_score: 6, audits_completed: 28,  alerts_forenses: 5,  risk_level: "low"    },
      { country_code: "FR", country_name: "Francia",        participation_pct: 2.0,  status: "Market Entry", influence_score: 4, audits_completed: 19,  alerts_forenses: 2,  risk_level: "low"    },
      { country_code: "IN", country_name: "India",          participation_pct: 1.5,  status: "Market Entry", influence_score: 5, audits_completed: 42,  alerts_forenses: 31, risk_level: "critical"},
      { country_code: "ES", country_name: "España",         participation_pct: 0.8,  status: "Market Entry", influence_score: 3, audits_completed: 15,  alerts_forenses: 4,  risk_level: "medium" },
      { country_code: "JP", country_name: "Japón",          participation_pct: 0.2,  status: "Market Entry", influence_score: 2, audits_completed: 8,   alerts_forenses: 1,  risk_level: "low"    },
      { country_code: "CA", country_name: "Canadá",         participation_pct: 0.0,  status: "Market Entry", influence_score: 2, audits_completed: 5,   alerts_forenses: 0,  risk_level: "low"    },
    ],
  },
  {
    id: "aerotech",
    name: "AeroTech Industries",
    sector: "Aerospace & Defense",
    affiliates: [
      { id: "aerotech-av",  name: "AeroTech Avionics Ltd",       role: "Avionics" },
      { id: "skyshield",    name: "SkyShield Defense Systems",   role: "Defense"  },
    ],
    countries: [
      { country_code: "US", country_name: "Estados Unidos", participation_pct: 45.0, status: "Established",  influence_score: 10, audits_completed: 312, alerts_forenses: 8,  risk_level: "low"    },
      { country_code: "DE", country_name: "Alemania",       participation_pct: 20.0, status: "Established",  influence_score: 8,  audits_completed: 96,  alerts_forenses: 11, risk_level: "low"    },
      { country_code: "FR", country_name: "Francia",        participation_pct: 12.0, status: "Expanding",    influence_score: 7,  audits_completed: 74,  alerts_forenses: 6,  risk_level: "low"    },
      { country_code: "GB", country_name: "Reino Unido",    participation_pct: 10.0, status: "Expanding",    influence_score: 8,  audits_completed: 88,  alerts_forenses: 4,  risk_level: "low"    },
      { country_code: "JP", country_name: "Japón",          participation_pct: 8.0,  status: "Expanding",    influence_score: 6,  audits_completed: 45,  alerts_forenses: 9,  risk_level: "medium" },
      { country_code: "CA", country_name: "Canadá",         participation_pct: 3.0,  status: "Market Entry", influence_score: 4,  audits_completed: 18,  alerts_forenses: 2,  risk_level: "low"    },
      { country_code: "CN", country_name: "China",          participation_pct: 2.0,  status: "Market Entry", influence_score: 3,  audits_completed: 12,  alerts_forenses: 18, risk_level: "high"   },
    ],
  },
  {
    id: "pacific",
    name: "Pacific Rim Holdings",
    sector: "Financial Services",
    affiliates: [
      { id: "pacific-fin",  name: "Pacific Finance Corp",      role: "Banking"    },
      { id: "rim-trading",  name: "Rim Trading Ltd",            role: "Trading"    },
      { id: "pacific-dig",  name: "Pacific Digital Services",  role: "Fintech"    },
    ],
    countries: [
      { country_code: "CN", country_name: "China",          participation_pct: 40.0, status: "Established",  influence_score: 10, audits_completed: 189, alerts_forenses: 67, risk_level: "critical"},
      { country_code: "JP", country_name: "Japón",          participation_pct: 25.0, status: "Established",  influence_score: 9,  audits_completed: 134, alerts_forenses: 22, risk_level: "medium" },
      { country_code: "IN", country_name: "India",          participation_pct: 15.0, status: "Expanding",    influence_score: 7,  audits_completed: 78,  alerts_forenses: 41, risk_level: "high"   },
      { country_code: "US", country_name: "Estados Unidos", participation_pct: 10.0, status: "Expanding",    influence_score: 8,  audits_completed: 102, alerts_forenses: 15, risk_level: "medium" },
      { country_code: "BR", country_name: "Brasil",         participation_pct: 3.0,  status: "Market Entry", influence_score: 4,  audits_completed: 21,  alerts_forenses: 8,  risk_level: "medium" },
      { country_code: "MX", country_name: "México",         participation_pct: 2.0,  status: "Market Entry", influence_score: 3,  audits_completed: 14,  alerts_forenses: 5,  risk_level: "medium" },
    ],
  },
  {
    id: "quantum",
    name: "Quantum Energy Corp",
    sector: "Energy",
    affiliates: [
      { id: "quantum-ren",  name: "Quantum Renewables",       role: "Solar/Wind"  },
      { id: "quantum-grid", name: "Quantum Grid Solutions",   role: "Grid Tech"   },
    ],
    countries: [
      { country_code: "US", country_name: "Estados Unidos", participation_pct: 30.0, status: "Established",  influence_score: 9,  audits_completed: 201, alerts_forenses: 12, risk_level: "low"    },
      { country_code: "CA", country_name: "Canadá",         participation_pct: 20.0, status: "Established",  influence_score: 8,  audits_completed: 98,  alerts_forenses: 7,  risk_level: "low"    },
      { country_code: "MX", country_name: "México",         participation_pct: 15.0, status: "Expanding",    influence_score: 7,  audits_completed: 67,  alerts_forenses: 19, risk_level: "medium" },
      { country_code: "BR", country_name: "Brasil",         participation_pct: 10.0, status: "Expanding",    influence_score: 6,  audits_completed: 54,  alerts_forenses: 11, risk_level: "medium" },
      { country_code: "DE", country_name: "Alemania",       participation_pct: 10.0, status: "Expanding",    influence_score: 7,  audits_completed: 61,  alerts_forenses: 4,  risk_level: "low"    },
      { country_code: "GB", country_name: "Reino Unido",    participation_pct: 8.0,  status: "Expanding",    influence_score: 6,  audits_completed: 43,  alerts_forenses: 3,  risk_level: "low"    },
      { country_code: "FR", country_name: "Francia",        participation_pct: 7.0,  status: "Market Entry", influence_score: 5,  audits_completed: 29,  alerts_forenses: 2,  risk_level: "low"    },
    ],
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function MapPlaceholder() {
  return (
    <div className="w-full h-full flex items-center justify-center">
      <motion.div
        className="w-10 h-10 border-2 border-red-600/40 rounded-full border-t-red-600"
        animate={{ rotate: 360 }}
        transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function IntelligencePage() {
  const pathname  = usePathname();
  const canvasRef = useRef<HTMLDivElement>(null);
  const threeRef  = useRef<{ renderer?: THREE.WebGLRenderer; animId?: number }>({});

  const [activeCompany,  setActiveCompany]  = useState<Company>(COMPANIES[0]);
  const [expandedId,     setExpandedId]     = useState<string | null>(COMPANIES[0].id);
  const [ticker] = useState([
    { label: "AUDITS_ACTIVE",  value: "847",  cls: "text-red-500"   },
    { label: "JURISDICTIONS",  value: "11",   cls: "text-yellow-400" },
    { label: "ALERTS_LIVE",    value: "312",  cls: "text-red-500"   },
    { label: "COMPLIANCE_AVG", value: "78.4%",cls: "text-green-500" },
  ]);

  // Three.js background (same as dashboard)
  useEffect(() => {
    if (!canvasRef.current) return;
    const scene    = new THREE.Scene();
    const camera   = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    canvasRef.current.appendChild(renderer.domElement);
    threeRef.current.renderer = renderer;

    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(3000 * 3);
    for (let i = 0; i < pPos.length; i++) pPos[i] = (Math.random() - 0.5) * 120;
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    const particles = new THREE.Points(
      pGeo,
      new THREE.PointsMaterial({ size: 0.04, color: 0xed1c24, transparent: true, opacity: 0.2 }),
    );
    scene.add(particles);

    // Globe wireframe
    const globe = new THREE.Mesh(
      new THREE.SphereGeometry(6, 24, 16),
      new THREE.MeshBasicMaterial({ color: 0xed1c24, wireframe: true, transparent: true, opacity: 0.04 }),
    );
    globe.position.set(18, -4, -15);
    scene.add(globe);

    camera.position.z = 20;
    scene.add(new THREE.AmbientLight(0xffffff, 0.05));

    const animate = () => {
      threeRef.current.animId = requestAnimationFrame(animate);
      particles.rotation.y += 0.0001;
      globe.rotation.y += 0.003;
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(threeRef.current.animId!);
      renderer.dispose();
      window.removeEventListener("resize", onResize);
      if (canvasRef.current && renderer.domElement.parentNode === canvasRef.current) {
        canvasRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  const toggleExpand = (company: Company) => {
    if (expandedId === company.id) {
      setExpandedId(null);
    } else {
      setExpandedId(company.id);
      setActiveCompany(company);
    }
  };

  const totalAudits  = activeCompany.countries.reduce((s, c) => s + c.audits_completed, 0);
  const totalAlerts  = activeCompany.countries.reduce((s, c) => s + c.alerts_forenses, 0);
  const topCountry   = [...activeCompany.countries].sort((a, b) => b.participation_pct - a.participation_pct)[0];

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden text-white">
      {/* Three.js canvas */}
      <div ref={canvasRef} className="absolute inset-0 z-[1]" />

      <div
        className="absolute inset-0 z-10 grid gap-4 p-6"
        style={{ gridTemplateColumns: "280px 1fr", gridTemplateRows: "60px 1fr 56px" }}
      >
        {/* ── Header ── */}
        <motion.header
          className="col-span-2 intel-glass flex justify-between items-center px-8"
          initial={{ opacity: 0, y: -18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
        >
          <div className="flex items-center gap-6">
            <h1 className="text-2xl font-black uppercase italic tracking-tighter">
              ATLAS <span className="text-white/20">GLOBAL_INTELLIGENCE</span>
            </h1>
            <div className="font-mono text-[8px] text-red-500 uppercase tracking-widest animate-pulse">
              ● 11_Jurisdictions_Active
            </div>
          </div>
          <Link href="/" className="text-[8px] font-black uppercase opacity-40 hover:opacity-100 transition-opacity tracking-widest">
            ← EXIT
          </Link>
        </motion.header>

        {/* ── Left: Company list + nav ── */}
        <motion.aside
          className="intel-glass flex flex-col overflow-hidden"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.45, delay: 0.08 }}
        >
          {/* Nav */}
          <nav className="flex-shrink-0">
            {NAV_LINKS.map(({ href, label }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`block px-4 py-3 border-l-2 transition-all text-[0.7rem] font-bold uppercase tracking-[0.1em] ${
                    active
                      ? "bg-red-600/5 border-l-red-600 text-white"
                      : "border-l-transparent text-slate-500 hover:bg-red-600/5 hover:border-l-red-600 hover:text-white"
                  }`}
                >
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* Divider */}
          <div className="border-t border-white/[0.04] my-1" />

          {/* Company list */}
          <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
            <div className="text-[7px] font-mono text-white/20 uppercase tracking-[0.4em] px-2 pb-1">
              Entities_Monitored
            </div>
            {COMPANIES.map((company) => {
              const isActive   = activeCompany.id === company.id;
              const isExpanded = expandedId === company.id;

              return (
                <div key={company.id}>
                  <motion.button
                    onClick={() => toggleExpand(company)}
                    className={`w-full text-left px-3 py-2.5 rounded border transition-all ${
                      isActive
                        ? "border-red-600/40 bg-red-600/5"
                        : "border-white/[0.04] bg-white/[0.01] hover:border-white/10 hover:bg-white/[0.02]"
                    }`}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[10px] font-bold text-white leading-tight">{company.name}</div>
                        <div className="text-[8px] text-white/30 font-mono mt-0.5">{company.sector}</div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className="text-[8px] font-mono text-red-500/70">
                          {company.countries.length} countries
                        </span>
                        <motion.span
                          className="text-[8px] text-white/20"
                          animate={{ rotate: isExpanded ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          ▾
                        </motion.span>
                      </div>
                    </div>
                  </motion.button>

                  {/* Affiliates */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="ml-3 pl-3 border-l border-red-900/30 py-1 space-y-0.5">
                          {company.affiliates.map((aff) => (
                            <div
                              key={aff.id}
                              className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-white/[0.02] transition-colors"
                            >
                              <div>
                                <div className="text-[9px] text-white/60 font-mono">{aff.name}</div>
                                <div className="text-[7px] text-white/20 font-mono">{aff.role}</div>
                              </div>
                              <div className="w-1.5 h-1.5 rounded-full bg-red-600/40" />
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>

          {/* Active company stats */}
          <div className="flex-shrink-0 border-t border-white/[0.04] p-4 space-y-2">
            <div className="text-[7px] font-mono text-red-500/60 uppercase tracking-[0.3em] mb-2">
              {activeCompany.name}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "Audits", value: totalAudits.toString(),   cls: "text-white"      },
                { label: "Alerts", value: totalAlerts.toString(),   cls: "text-red-500"    },
                { label: "Top Mkt", value: topCountry?.country_code ?? "—", cls: "text-yellow-400" },
                { label: "Peak %",  value: `${topCountry?.participation_pct ?? 0}%`, cls: "text-green-400" },
              ].map((s) => (
                <div key={s.label} className="bg-white/[0.02] rounded p-2">
                  <div className="text-[7px] text-white/20 font-mono uppercase">{s.label}</div>
                  <div className={`text-sm font-black font-mono ${s.cls}`}>{s.value}</div>
                </div>
              ))}
            </div>
          </div>
        </motion.aside>

        {/* ── Right: Holographic World Map ── */}
        <motion.main
          className="intel-glass relative overflow-hidden"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.14 }}
        >
          {/* Map header */}
          <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-5 py-3 border-b border-white/[0.04]">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-[9px] font-mono font-bold uppercase tracking-[0.3em] text-red-500">
                Market_Footprint_Hologram
              </span>
            </div>
            <div className="flex items-center gap-4 text-[8px] font-mono text-white/20">
              <span>{activeCompany.countries.length} JURISDICTIONS</span>
              <span className="text-red-500/50">●</span>
              <span>LIVE_INTEL</span>
            </div>
          </div>

          {/* Map body */}
          <div className="absolute inset-0 top-10 bottom-0">
            <WorldMap
              key={activeCompany.id}
              data={activeCompany.countries}
            />
          </div>
        </motion.main>

        {/* ── Footer ticker ── */}
        <motion.footer
          className="col-span-2 intel-glass flex items-center overflow-hidden px-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.2 }}
        >
          <div className="text-[7px] font-mono text-red-500/50 uppercase tracking-widest shrink-0 mr-4">
            INTEL_STREAM ●
          </div>
          <div className="flex-1 overflow-hidden">
            <div className="flex gap-8 font-mono text-[9px] whitespace-nowrap animate-[ticker_20s_linear_infinite]">
              {[...ticker, ...ticker].map((t, i) => (
                <span key={i} className="shrink-0 text-white/40">
                  {t.label}: <span className={t.cls}>{t.value}</span>
                </span>
              ))}
            </div>
          </div>
        </motion.footer>
      </div>

      <style jsx>{`
        .intel-glass {
          background: rgba(255, 255, 255, 0.015);
          border: 1px solid rgba(237, 28, 36, 0.12);
          backdrop-filter: blur(24px);
          position: relative;
          overflow: hidden;
        }
        .intel-glass::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 2px; height: 100%;
          background: linear-gradient(to bottom, #ED1C24, transparent);
          pointer-events: none;
        }
        @keyframes ticker {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
