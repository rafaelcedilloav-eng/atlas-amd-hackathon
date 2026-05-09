"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as THREE from "three";
import { FlaskConical, AlertTriangle, CheckCircle2, Zap, ArrowRight, ShieldAlert, TrendingUp } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

// ─── Types ───────────────────────────────────────────────────────────────────
interface HeatMapEntry {
  jurisdiction: string;
  risk_level: string;
  probability_violation: number;
  financial_impact_usd: number;
  reaction_deadline_days: number;
  confidence: string;
}
interface TimelineEvent {
  date_offset_days: number;
  event: string;
  risk_level: string;
  mandatory_action: string;
  penalty_if_missed: string;
}
interface CompoundRisk {
  risk_id: string;
  description: string;
  cascade_effect: string;
  severity: string;
}
interface AlternativeScenario {
  alternative_id: string;
  description: string;
  risk_mitigation: string;
  cost_impact: string;
}
interface SandboxResult {
  id: string;
  mode: string;
  simulation_engine: {
    regulatory_heat_map: HeatMapEntry[];
    timeline: TimelineEvent[];
    compound_risks: CompoundRisk[];
    alternative_scenarios: AlternativeScenario[];
  };
  output: {
    overall_risk_score: number;
    recommendation: string;
    executive_summary: string;
    confidence: string;
    source_status: string;
  };
  metadata?: { demo_mode?: boolean };
}

// ─── Demo fallback (sandbox-002) ─────────────────────────────────────────────
const DEMO_DATA: SandboxResult = {
  id: "sandbox-demo-002",
  mode: "sandbox",
  simulation_engine: {
    regulatory_heat_map: [
      { jurisdiction: "MX (IVA)", risk_level: "CRITICO", probability_violation: 0.90, financial_impact_usd: 278400, reaction_deadline_days: 15, confidence: "high" },
      { jurisdiction: "MX (Art. 30-B)", risk_level: "alto", probability_violation: 0.70, financial_impact_usd: 50000, reaction_deadline_days: 30, confidence: "medium" },
      { jurisdiction: "USA (CA Sales Tax)", risk_level: "medio", probability_violation: 0.60, financial_impact_usd: 87000, reaction_deadline_days: 90, confidence: "high" },
      { jurisdiction: "USA (TX Sales Tax)", risk_level: "medio", probability_violation: 0.55, financial_impact_usd: 52200, reaction_deadline_days: 90, confidence: "high" },
    ],
    timeline: [
      { date_offset_days: 0, event: "Inicio ventas SaaS a MX", risk_level: "CRITICO", mandatory_action: "Mecanismo de retención IVA 16% operativo", penalty_if_missed: "Multas SAT por omisión de retención + actualizaciones + recargos" },
      { date_offset_days: 15, event: "Declaración IVA mensual", risk_level: "alto", mandatory_action: "Enterar IVA retenido ante SAT", penalty_if_missed: "Recargos del 1.47% mensual + multas" },
      { date_offset_days: 90, event: "Sales Tax Filing Q3 CA/TX/NY", risk_level: "medio", mandatory_action: "Declarar y remitir sales tax por estado", penalty_if_missed: "Multas estatales + intereses" },
    ],
    compound_risks: [
      { risk_id: "CP-002", description: "No registro Art. 18-D + no retención IVA + Art. 30-B = triple incumplimiento que puede generar bloqueo de pagos por adquirentes mexicanos.", cascade_effect: "Adquirente bancario MX bloquea transacciones → corte de ingresos.", severity: "CRITICO" },
    ],
    alternative_scenarios: [
      { alternative_id: "ALT-003", description: "Registro Art. 18-D LIVA elimina riesgo de bloqueo por adquirente y asume control directo de retención IVA.", risk_mitigation: "Control directo del cumplimiento IVA", cost_impact: "Registro SAT + contador local MX + sistema facturación" },
      { alternative_id: "ALT-004", description: "Venta exclusivamente vía App Store/Google Play traslada la retención al marketplace.", risk_mitigation: "Cumplimiento delegado al marketplace", cost_impact: "Margen reducido 15-30%" },
    ],
  },
  output: {
    overall_risk_score: 78.0,
    recommendation: "RESTRUCTURE_BEFORE_EXECUTING",
    executive_summary: "Operación de ALTO RIESGO. La venta directa de SaaS a MX sin mecanismo de retención IVA activa viola Art. 18-J LIVA. Requiere: (1) registro Art. 18-D LIVA, (2) integración con adquirente mexicano para retención automática, o (3) venta vía marketplace. Sales tax en CA/TX es manejable con registro preventivo.",
    confidence: "high",
    source_status: "official",
  },
  metadata: { demo_mode: false },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────
function riskClass(level: string) {
  const l = level.toLowerCase();
  if (l === "critico") return "critical";
  if (l === "alto") return "high";
  if (l === "medio") return "medium";
  return "low";
}
function scoreClass(score: number) {
  if (score >= 80) return "text-red-500 drop-shadow-[0_0_12px_rgba(239,68,68,0.6)]";
  if (score >= 60) return "text-yellow-400 drop-shadow-[0_0_12px_rgba(234,179,8,0.5)]";
  if (score >= 40) return "text-[#00D4FF] drop-shadow-[0_0_12px_rgba(0,212,255,0.5)]";
  return "text-green-400 drop-shadow-[0_0_12px_rgba(74,222,128,0.5)]";
}
function barColor(level: string) {
  const l = level.toLowerCase();
  if (l === "critico") return "bg-red-500 shadow-[0_0_10px_#ED1C24]";
  if (l === "alto") return "bg-yellow-400 shadow-[0_0_10px_#FFB800]";
  if (l === "medio") return "bg-[#00D4FF] shadow-[0_0_10px_#00D4FF]";
  return "bg-green-400 shadow-[0_0_10px_#00D966]";
}
function recStyle(rec: string) {
  if (rec === "ABORT") return { cls: "border-red-500 bg-red-500/10 text-red-400", label: "🚫 ABORTAR OPERACIÓN" };
  if (rec === "RESTRUCTURE_BEFORE_EXECUTING") return { cls: "border-yellow-400 bg-yellow-400/10 text-yellow-400", label: "🔧 RESTRUCTURE BEFORE EXECUTING" };
  if (rec === "ESCALATE_LEGAL") return { cls: "border-yellow-400 bg-yellow-400/10 text-yellow-400", label: "⚖️ ESCALAR A LEGAL" };
  return { cls: "border-[#00D4FF] bg-[#00D4FF]/10 text-[#00D4FF]", label: "⚠️ PROCEED WITH CAUTION" };
}
function getFlag(j: string) {
  if (j.includes("MX")) return "🇲🇽";
  if (j.match(/USA|CA |TX |NY /)) return "🇺🇸";
  return "🌐";
}

// ─── Component ───────────────────────────────────────────────────────────────
export default function SandboxPage() {
  const canvasRef = useRef<HTMLDivElement>(null);
  const threeRef = useRef<{ renderer?: THREE.WebGLRenderer; animId?: number }>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SandboxResult | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [redTeam, setRedTeam] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  const [form, setForm] = useState({
    description: "",
    type: "constitucion_LLC",
    date: "2026-06-15",
    value: "500000",
    jurisdiction: "MX",
    mode: "sandbox",
    ubos: "false",
  });

  // Three.js background (match dashboard pattern)
  useEffect(() => {
    if (!canvasRef.current) return;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    canvasRef.current.appendChild(renderer.domElement);
    threeRef.current.renderer = renderer;

    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(1500 * 3);
    for (let i = 0; i < pPos.length; i++) pPos[i] = (Math.random() - 0.5) * 80;
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    const particles = new THREE.Points(
      pGeo,
      new THREE.PointsMaterial({ size: 0.04, color: 0x00d4ff, transparent: true, opacity: 0.2 }),
    );
    scene.add(particles);

    const grid = new THREE.GridHelper(200, 40, 0x2a2a3f, 0x1a1a1f);
    grid.position.y = -10;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.1;
    scene.add(grid);

    camera.position.z = 30;

    const clock = new THREE.Clock();
    function animate() {
      threeRef.current.animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      particles.rotation.y += 0.0001;
      particles.rotation.z += 0.0001;
      grid.position.z = (t * 2) % 10;
      renderer.render(scene, camera);
    }
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
    };
  }, []);

  const set = (k: string, v: string) => {
    setForm((f) => ({ ...f, [k]: v }));
    if (k === "mode") setRedTeam(v === "red_team");
  };

  async function simulate() {
    if (!form.description.trim()) return;
    setLoading(true);
    setResult(null);
    setDemoMode(false);

    try {
      const res = await fetch(`${API_BASE}/api/v1/sandbox/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation_description: form.description,
          operation_details: {
            type: form.type,
            value_usd: Number(form.value),
            has_mexican_ubos: form.ubos === "true",
            primary_jurisdiction: form.jurisdiction,
          },
          proposed_date: form.date,
          mode: form.mode,
        }),
        signal: AbortSignal.timeout(60_000),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: SandboxResult = await res.json();
      setDemoMode(data.metadata?.demo_mode === true);
      setResult(data);
    } catch {
      setDemoMode(true);
      setResult({ ...DEMO_DATA, mode: form.mode });
    } finally {
      setLoading(false);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth" }), 200);
    }
  }

  const rec = result ? recStyle(result.output.recommendation) : null;

  return (
    <div className="relative min-h-screen bg-[#0A0A0C] text-white font-mono overflow-x-hidden">
      {/* Immersive Background */}
      <div ref={canvasRef} className="fixed inset-0 z-0 pointer-events-none opacity-40" />
      
      <div className="relative z-10 max-w-6xl mx-auto px-6 py-12">
        {/* Header (Refined ATLAS style) */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#00D4FF]/20 bg-[#00D4FF]/5 text-[#00D4FF] text-[10px] font-bold uppercase tracking-[0.2em] mb-4">
            <Zap className="w-3 h-3" />
            Predictive Intelligence Engine
          </div>
          <h1 className="text-4xl md:text-5xl font-black uppercase italic tracking-tighter text-white">
            ATLAS <span className="text-[#00D4FF]">REGULATORY</span> <span className="text-[#ED1C24]">SANDBOX</span>
          </h1>
          <div className="flex items-center justify-center gap-6 mt-4 font-mono text-[10px] text-gray-500 uppercase tracking-widest">
            <span>AMD_MI300X_ACCELERATED</span>
            <span className="text-[#ED1C24]">●</span>
            <span>QWEN3_FINETUNED_V1.0</span>
          </div>
        </motion.div>

        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`glass-card p-8 mb-12 transition-all duration-500 relative ${
            redTeam ? "border-red-500/40 shadow-[0_0_40px_rgba(237,28,36,0.1)]" : "border-[#2A2A3F]"
          }`}
        >
          {/* Top accent border */}
          <div className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${redTeam ? "from-red-600 to-red-900" : "from-[#00D4FF] to-[#ED1C24]"}`} />
          
          <h2 className={`text-sm font-black uppercase italic mb-6 flex items-center gap-2 ${redTeam ? "text-red-500" : "text-[#00D4FF]"}`}>
            <FlaskConical className="w-4 h-4" />
            Simulation_Protocol_Input
            {redTeam && <span className="text-red-400 animate-pulse ml-2 tracking-[0.3em]">● RED_TEAM_MODE_ACTIVE</span>}
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-8 space-y-6">
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Operation_Description</label>
                <textarea
                  className="w-full bg-black/40 border border-[#2A2A3F] rounded-lg px-4 py-3 text-sm text-white resize-none min-h-[140px] focus:outline-none focus:border-[#00D4FF] focus:bg-[#00D4FF]/5 transition-all duration-300"
                  placeholder="Ej: Proposing a cross-border SaaS operation from Mexico to Delaware involving UBOs with tax residency in Jalisco..."
                  value={form.description}
                  onChange={(e) => set("description", e.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Simulation_Type</label>
                  <select
                    className="w-full bg-black/40 border border-[#2A2A3F] rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-[#00D4FF] transition-all"
                    value={form.type}
                    onChange={(e) => set("type", e.target.value)}
                  >
                    {[["constitucion_LLC","Constitución LLC"],["venta_digital","Venta Digital/SaaS"],["contrato_servicios","Contrato de Servicios"],["operacion_combustible","Operación Combustible"],["fusion_adquisicion","Fusión/Adquisición"],["adquisicion_activo","Adquisición de Activo"]].map(([v, l]) => <option key={v} value={v} className="bg-[#1A1A1F]">{l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Risk_Mode</label>
                  <select
                    className="w-full bg-black/40 border border-[#2A2A3F] rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-[#00D4FF] transition-all"
                    value={form.mode}
                    onChange={(e) => set("mode", e.target.value)}
                  >
                    {[["sandbox","Standard Analysis"],["red_team","🔴 Red Team Mode"]].map(([v, l]) => <option key={v} value={v} className="bg-[#1A1A1F]">{l}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div className="lg:col-span-4 space-y-6 bg-black/20 p-6 rounded-lg border border-[#2A2A3F]/50">
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Target_Jurisdiction</label>
                <select className="w-full bg-black/40 border border-[#2A2A3F] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00D4FF]" value={form.jurisdiction} onChange={(e) => set("jurisdiction", e.target.value)}>
                  {[["MX","México"],["USA","Estados Unidos"],["CROSS","Cross-border"]].map(([v, l]) => <option key={v} value={v} className="bg-[#1A1A1F]">{l}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Proposed_Date</label>
                <input type="date" className="w-full bg-black/40 border border-[#2A2A3F] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00D4FF]" value={form.date} onChange={(e) => set("date", e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Operation_Value (USD)</label>
                <input type="number" className="w-full bg-black/40 border border-[#2A2A3F] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00D4FF]" value={form.value} onChange={(e) => set("value", e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Mexican_UBOs</label>
                <select className="w-full bg-black/40 border border-[#2A2A3F] rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00D4FF]" value={form.ubos} onChange={(e) => set("ubos", e.target.value)}>
                  <option value="false" className="bg-[#1A1A1F]">No</option>
                  <option value="true" className="bg-[#1A1A1F]">Sí</option>
                </select>
              </div>
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.02, boxShadow: "0 0 40px rgba(237,28,36,0.6)" }}
            whileTap={{ scale: 0.98 }}
            onClick={simulate}
            disabled={loading}
            className={`w-full mt-8 py-4 rounded-lg font-black text-sm uppercase tracking-[0.2em] transition-all duration-300 flex items-center justify-center gap-3
              ${loading ? "bg-gray-800 text-gray-500 cursor-not-allowed" : "bg-red-600 text-white shadow-[0_0_25px_rgba(237,28,36,0.35)]"}
            `}
          >
            {loading ? (
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
                Processing_Neural_Engine...
              </div>
            ) : (
              <>
                <Zap className="w-5 h-5 fill-white" />
                Initiate_Simulation_Protocol
              </>
            )}
          </motion.button>
        </motion.div>

        {/* Results with AnimatePresence */}
        <AnimatePresence mode="wait">
          {loading ? (
             <motion.div 
               key="loading"
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               exit={{ opacity: 0 }}
               className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
             >
                {[1,2,3].map(i => (
                  <div key={i} className="glass-card h-64 animate-pulse bg-white/5 border border-white/10 rounded-lg" />
                ))}
             </motion.div>
          ) : result && (
            <motion.div 
              key="results"
              ref={resultsRef} 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8"
            >
              {demoMode && (
                <div className="flex items-center gap-3 px-4 py-3 bg-yellow-400/5 border border-yellow-400/20 rounded-lg text-yellow-500 text-[10px] font-bold uppercase tracking-widest">
                  <AlertTriangle className="w-4 h-4" />
                  Demo Mode: Analysis generated from local cache (sandbox-002)
                </div>
              )}

              {/* Main Score & Recommendation */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="lg:col-span-4 glass-card p-8 flex flex-col items-center justify-center text-center relative"
                >
                  <div className="absolute top-0 left-0 right-0 h-[2px] bg-[#ED1C24]" />
                  <div className="text-[10px] font-black text-gray-500 uppercase tracking-[0.4em] mb-6">Risk_Signature</div>
                  <div className={`text-8xl font-black italic leading-none mb-4 ${scoreClass(result.output.overall_risk_score)}`}>
                    {result.output.overall_risk_score.toFixed(0)}
                  </div>
                  <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden mb-6">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${result.output.overall_risk_score}%` }}
                      className={`h-full ${barColor("critico")}`}
                    />
                  </div>
                  <div className={`w-full py-4 rounded border text-xs font-black uppercase tracking-[0.1em] ${rec!.cls}`}>
                    {rec!.label}
                  </div>
                </motion.div>

                <motion.div 
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="lg:col-span-8 glass-card p-8 relative"
                >
                  <div className="absolute top-0 left-0 right-0 h-[2px] bg-[#00D4FF]" />
                  <h3 className="text-[#00D4FF] text-xs font-black uppercase italic tracking-widest mb-6 border-b border-[#00D4FF]/20 pb-2 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Executive_Reasoning_Summary
                  </h3>
                  <div className="bg-black/40 rounded-lg p-6 border border-[#2A2A3F]">
                    <p className="text-gray-300 text-sm leading-relaxed font-light italic">
                      &ldquo;{result.output.executive_summary}&rdquo;
                    </p>
                  </div>
                  <div className="mt-6 flex justify-between items-center text-[9px] font-bold text-gray-600 uppercase tracking-[0.2em]">
                    <span>CONFIDENCE: {result.output.confidence.toUpperCase()}</span>
                    <span>SOURCE: {result.output.source_status.toUpperCase()}</span>
                  </div>
                </motion.div>
              </div>

              {/* Heat Map Section */}
              <div className="glass-card p-8 relative">
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#00D4FF] to-[#ED1C24]" />
                <h3 className="text-white text-xs font-black uppercase italic tracking-[0.2em] mb-8 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#00D4FF]" />
                  Regulatory_Heat_Map // 12_Month_Projection
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {result.simulation_engine.regulatory_heat_map.map((item, i) => (
                    <motion.div 
                      key={i} 
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className="bg-black/30 border border-[#2A2A3F] rounded-lg p-5 hover:border-[#00D4FF]/40 transition-all group"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{getFlag(item.jurisdiction)}</span>
                          <span className="text-[11px] font-black uppercase text-white tracking-wider group-hover:text-[#00D4FF] transition-colors">
                            {item.jurisdiction}
                          </span>
                        </div>
                        <span className={`text-[9px] font-black px-2 py-1 rounded-sm ${barColor(item.risk_level)} text-black uppercase`}>
                          {item.risk_level}
                        </span>
                      </div>
                      
                      <div className="space-y-3">
                        <div className="relative pt-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[9px] text-gray-500 uppercase font-bold tracking-widest">Probability_of_Violation</span>
                            <span className="text-[9px] font-black text-[#00D4FF]">{(item.probability_violation * 100).toFixed(0)}%</span>
                          </div>
                          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${(item.probability_violation * 100).toFixed(0)}%` }}
                              className={`h-full ${barColor(item.risk_level)}`}
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4 pt-2">
                          <div>
                            <div className="text-[8px] text-gray-600 uppercase font-bold mb-1">Impact_USD</div>
                            <div className="text-xs font-black text-white">${item.financial_impact_usd.toLocaleString()}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-[8px] text-gray-600 uppercase font-bold mb-1">Reaction_Limit</div>
                            <div className="text-xs font-black text-white">{item.reaction_deadline_days} Days</div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Timeline & Compound Risks */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Timeline */}
                <div className="glass-card p-8">
                  <h3 className="text-white text-xs font-black uppercase italic tracking-[0.2em] mb-8">Critical_Timeline</h3>
                  <div className="relative pl-6 space-y-8">
                    <div className="absolute left-1.5 top-0 bottom-0 w-px bg-gradient-to-b from-[#00D4FF] via-[#ED1C24] to-transparent opacity-30" />
                    {result.simulation_engine.timeline.map((item, i) => (
                      <motion.div 
                        key={i} 
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="relative group"
                      >
                        <div className="absolute -left-[23px] top-1.5 w-3 h-3 rounded-full bg-black border border-[#00D4FF] group-hover:bg-[#00D4FF] transition-all shadow-[0_0_10px_rgba(0,212,255,0.4)]" />
                        <div className="text-[#00D4FF] text-[9px] font-black mb-1">DAY_T+{item.date_offset_days}</div>
                        <div className="text-sm font-black text-white uppercase mb-2 group-hover:text-[#00D4FF] transition-colors">{item.event}</div>
                        <div className="bg-white/[0.03] p-3 rounded-r-lg border-l-2 border-red-500/30">
                          <div className="text-[10px] text-gray-400 font-medium mb-2 uppercase leading-relaxed tracking-tight">
                            <span className="text-red-500/50 mr-2">ACTION:</span> {item.mandatory_action}
                          </div>
                          <div className="text-[9px] text-red-400 font-bold uppercase tracking-tighter italic">
                             ⚠️ {item.penalty_if_missed}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Compound & Scenarios */}
                <div className="space-y-8">
                  {/* Compound Risks */}
                  {result.simulation_engine.compound_risks.length > 0 && (
                    <div className="glass-card p-8 border-r-4 border-r-red-600">
                      <h3 className="text-red-500 text-xs font-black uppercase italic tracking-[0.2em] mb-6 flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4" />
                        Cascade_Risk_Detection
                      </h3>
                      {result.simulation_engine.compound_risks.map((risk, i) => (
                        <motion.div 
                          key={i} 
                          initial={{ scale: 0.98 }}
                          whileHover={{ scale: 1 }}
                          className="bg-red-600/5 border border-red-500/20 rounded-lg p-5 mb-4"
                        >
                          <div className="text-red-500 text-[10px] font-black mb-2">{risk.risk_id}</div>
                          <div className="text-sm text-gray-200 font-medium leading-relaxed mb-3">{risk.description}</div>
                          <div className="text-yellow-500 text-[9px] font-black uppercase tracking-widest italic flex items-center gap-2">
                            <ArrowRight className="w-3 h-3" />
                            CASCADE_EFFECT: {risk.cascade_effect}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  {/* Scenarios */}
                  <div className="glass-card p-8 border-r-4 border-r-green-600">
                    <h3 className="text-green-500 text-xs font-black uppercase italic tracking-[0.2em] mb-6 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Mitigation_Paths
                    </h3>
                    {result.simulation_engine.alternative_scenarios.map((alt, i) => (
                      <div key={i} className="bg-green-600/5 border border-green-500/10 rounded-lg p-5 mb-4 group">
                        <div className="text-green-500 text-[10px] font-black mb-2">{alt.alternative_id}</div>
                        <div className="text-sm text-gray-300 font-medium leading-relaxed mb-3 group-hover:text-white transition-colors">{alt.description}</div>
                        <div className="grid grid-cols-2 gap-4 text-[9px] font-black uppercase tracking-tighter">
                          <div className="text-gray-500">COST: <span className="text-white">{alt.cost_impact}</span></div>
                          <div className="text-right text-[#00D4FF]">SHIELD: <span className="text-green-500">{alt.risk_mitigation}</span></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style jsx>{`
        .glass-card {
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(24px);
          border-radius: 12px;
          position: relative;
          overflow: hidden;
        }
        .glass-card::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 2px; height: 100%;
          background: linear-gradient(to bottom, #ED1C24, transparent);
          pointer-events: none;
        }
      `}</style>
    </div>
  );
}
