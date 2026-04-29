"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import * as THREE from "three";
import gsap from "gsap";
import { Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  type ChartOptions,
} from "chart.js";
import type { Chart as ChartType } from "chart.js";

ChartJS.register(ArcElement, Tooltip);

type AgentKey = "vision" | "reasoning" | "integrity" | "explainer";

const AGENTS: Record<AgentKey, {
  name: string; role: string; model: string; load: string; loadPct: number;
  color: string; desc: string; chartIdx: number;
}> = {
  vision: {
    name: "Vision_Extractor", role: "OCR & Spatial Mapping",
    model: "Gemini 1.5 Flash", load: "74%", loadPct: 74,
    color: "bg-red-600", chartIdx: 0,
    desc: "High-resolution OCR and spatial entity extraction. Maps document Z-layers for forensic proof of tampering.",
  },
  reasoning: {
    name: "Reasoning_Unit", role: "Logic Engine",
    model: "DeepSeek-R1", load: "30%", loadPct: 30,
    color: "bg-blue-600", chartIdx: 1,
    desc: "Executes deep chain-of-thought to find contradictory clauses and hidden fraud patterns in extracted data.",
  },
  integrity: {
    name: "Integrity_Gate", role: "Security Gate",
    model: "Heuristics_v2", load: "15%", loadPct: 15,
    color: "bg-purple-600", chartIdx: 2,
    desc: "Validates document integrity hashes and buckets findings into security classes for the decision pipeline.",
  },
  explainer: {
    name: "Explainer_AI", role: "Report Synthesis",
    model: "Gemini 1.5 Pro", load: "10%", loadPct: 10,
    color: "bg-gray-600", chartIdx: 3,
    desc: "Synthesizes complex forensic data into actionable executive summaries for legal and compliance teams.",
  },
};

const AGENT_KEYS = Object.keys(AGENTS) as AgentKey[];

const DONUT_DATA = {
  labels:   ["Vision", "Reasoning", "Integrity", "Explainer"],
  datasets: [{
    data:            [45, 30, 15, 10],
    backgroundColor: ["#ED1C24", "#0078ff", "#bc00ff", "#444444"],
    borderWidth:     0,
    hoverOffset:     15,
  }],
};

const DONUT_OPTIONS: ChartOptions<"doughnut"> = {
  cutout:  "85%",
  plugins: { legend: { display: false } },
};

export default function HardwarePage() {
  const canvasRef = useRef<HTMLDivElement>(null);
  const threeRef  = useRef<{ renderer?: THREE.WebGLRenderer; animId?: number; camera?: THREE.PerspectiveCamera }>({});
  const mouseRef  = useRef({ x: 0, y: 0 });
  const chartRef  = useRef<ChartType<"doughnut"> | null>(null);

  const [activeAgent, setActiveAgent] = useState<AgentKey | null>(null);

  // Three.js
  useEffect(() => {
    if (!canvasRef.current) return;
    const scene    = new THREE.Scene();
    const camera   = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    canvasRef.current.appendChild(renderer.domElement);
    threeRef.current.renderer = renderer;
    threeRef.current.camera   = camera;

    // Grid floor
    const grid = new THREE.GridHelper(200, 60, 0xed1c24, 0x111111);
    grid.position.y = -10;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity     = 0.2;
    scene.add(grid);

    // Particles
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(10000 * 3);
    for (let i = 0; i < pPos.length; i++) pPos[i] = (Math.random() - 0.5) * 150;
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    const particles = new THREE.Points(
      pGeo,
      new THREE.PointsMaterial({ size: 0.1, color: 0xed1c24, transparent: true, opacity: 0.3 }),
    );
    scene.add(particles);

    // Core
    const core = new THREE.Mesh(
      new THREE.IcosahedronGeometry(6, 2),
      new THREE.MeshStandardMaterial({ color: 0xed1c24, wireframe: true, emissive: 0xed1c24, emissiveIntensity: 0.2, transparent: true, opacity: 0.1 }),
    );
    scene.add(core);

    scene.add(new THREE.AmbientLight(0xffffff, 0.1));
    const pl = new THREE.PointLight(0xed1c24, 2, 100);
    pl.position.set(10, 10, 10);
    scene.add(pl);
    camera.position.z = 25;

    const clock = new THREE.Clock();
    function animate() {
      threeRef.current.animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      particles.rotation.y += 0.0002;
      core.rotation.y      += 0.005;
      grid.position.z       = (t * 2) % 10;
      camera.position.x    += (mouseRef.current.x * 6 - camera.position.x) * 0.05;
      camera.position.y    += (mouseRef.current.y * 4 - camera.position.y) * 0.05;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
    }
    animate();

    const onMove   = (e: MouseEvent) => {
      mouseRef.current.x = (e.clientX / window.innerWidth)  *  2 - 1;
      mouseRef.current.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("resize",    onResize);

    return () => {
      cancelAnimationFrame(threeRef.current.animId!);
      renderer.dispose();
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("resize",    onResize);
      if (canvasRef.current && renderer.domElement.parentNode === canvasRef.current) {
        canvasRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  const focusAgent = (id: AgentKey) => {
    setActiveAgent(id);
    // Highlight chart segment
    if (chartRef.current) {
      chartRef.current.setActiveElements([{ datasetIndex: 0, index: AGENTS[id].chartIdx }]);
      chartRef.current.update();
    }
    // Camera zoom in
    if (threeRef.current.camera) {
      gsap.to(threeRef.current.camera.position, { z: 20, duration: 1, ease: "power2.out" });
    }
  };

  const hideAgent = () => {
    setActiveAgent(null);
    if (chartRef.current) {
      chartRef.current.setActiveElements([]);
      chartRef.current.update();
    }
    if (threeRef.current.camera) {
      gsap.to(threeRef.current.camera.position, { z: 25, duration: 1, ease: "power2.out" });
    }
  };

  const agent = activeAgent ? AGENTS[activeAgent] : null;

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden text-white">
      <div ref={canvasRef} className="absolute inset-0 z-[1]" />

      <div
        className="absolute inset-0 z-10 grid gap-6 p-10"
        style={{ gridTemplateColumns: "320px 1fr 320px", gridTemplateRows: "auto 1fr auto" }}
      >
        {/* Header */}
        <header className="col-span-3 flex justify-between items-center">
          <div className="flex items-center gap-8">
            <Link href="/dashboard" className="btn-hw">← TERMINAL_EXIT</Link>
            <h1 className="text-5xl font-black uppercase italic tracking-tighter">
              ORCHESTRATOR<span className="text-red-600">_NODE</span>
            </h1>
          </div>
          <div className="font-mono text-[10px] text-red-500 uppercase tracking-widest">
            Inference_Engine_v2.5 // AMD
          </div>
        </header>

        {/* Left: Hardware + Token chart */}
        <aside className="space-y-6 overflow-y-auto">
          <div className="glass-hw p-6">
            <h3 className="text-[10px] font-black uppercase text-red-500 mb-6 tracking-widest">
              Hardware_Telemetry
            </h3>
            <div className="space-y-6">
              <TelemetryBar label="MI300X_LOAD" value="74%" pct={74} />
              <TelemetryBar label="HBM3_USAGE"  value="124GB" pct={82} />
              <TelemetryBar label="ROCm_THREADS" value="92%" pct={92} />
              <TelemetryBar label="VRAM_POOL"    value="192GB" pct={65} />
            </div>
          </div>

          <div className="glass-hw p-6">
            <h3 className="text-[10px] font-black uppercase text-red-500 mb-4 tracking-widest">
              Token_Distribution
            </h3>
            <div style={{ height: 220 }}>
              <Doughnut
                ref={chartRef as any}
                data={DONUT_DATA}
                options={DONUT_OPTIONS}
              />
            </div>
            <div className="grid grid-cols-2 gap-2 mt-4">
              {DONUT_DATA.labels.map((label, i) => (
                <div key={label} className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ background: (DONUT_DATA.datasets[0].backgroundColor as string[])[i] }}
                  />
                  <span className="font-mono text-[9px] text-gray-500">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Center: Agent info panel */}
        <main className="relative flex items-center justify-center">
          <div
            className={`glass-hw p-10 max-w-lg w-full border-white/20 shadow-[0_0_50px_rgba(237,28,36,0.1)] transition-all duration-500 ${
              activeAgent ? "opacity-100 scale-100 pointer-events-auto" : "opacity-0 scale-90 pointer-events-none"
            }`}
          >
            {agent && (
              <>
                <div className="text-2xl font-black uppercase italic text-red-500 mb-2">
                  {agent.name}
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest mb-6 border-b border-white/10 pb-2 text-gray-400">
                  {agent.role}
                </div>
                <p className="text-sm text-gray-300 leading-relaxed italic mb-8">
                  {agent.desc}
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white/5 p-4 border border-white/5">
                    <div className="text-[8px] text-gray-500 uppercase mb-1">Model</div>
                    <div className="text-xs font-bold">{agent.model}</div>
                  </div>
                  <div className="bg-white/5 p-4 border border-white/5">
                    <div className="text-[8px] text-gray-500 uppercase mb-1">Load</div>
                    <div className="text-xs font-bold text-red-500">{agent.load}</div>
                  </div>
                </div>
                <div className="mt-8 flex justify-center">
                  <button onClick={hideAgent} className="btn-hw text-[8px] px-10">
                    CLOSE_DEEP_DIVE
                  </button>
                </div>
              </>
            )}
          </div>
        </main>

        {/* Right: Agent cards */}
        <aside className="space-y-4 overflow-y-auto">
          <h3 className="text-[10px] font-black uppercase text-red-500 mb-4 tracking-widest text-right">
            AI_Cluster_Management
          </h3>
          {AGENT_KEYS.map((key) => {
            const a       = AGENTS[key];
            const isActive = activeAgent === key;
            return (
              <div
                key={key}
                onClick={() => focusAgent(key)}
                className={`p-4 border cursor-pointer transition-all duration-300 ${
                  isActive
                    ? "border-white bg-white/5"
                    : "border-white/5 bg-white/[0.01] hover:border-red-600 hover:-translate-x-1.5"
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-bold">{a.name}</div>
                  <div className={`w-2 h-2 rounded-full ${a.color} ${key === "vision" ? "animate-pulse" : ""}`} />
                </div>
                <div className="font-mono text-[9px] text-gray-500 mb-2">{a.role}</div>
                <div className="h-px bg-white/10 relative overflow-hidden">
                  <div
                    className="absolute inset-0 bg-red-600"
                    style={{ width: `${a.loadPct}%` }}
                  />
                </div>
                <div className="font-mono text-[8px] text-gray-600 mt-1 text-right">{a.load}</div>
              </div>
            );
          })}
        </aside>

        {/* Footer */}
        <footer className="col-span-3 mt-4 flex justify-between border-t border-white/5 pt-4">
          <div className="font-mono text-[8px] opacity-30 tracking-[1em]">AMD // ROCm // INSTINCT</div>
          <div className="text-[9px] text-red-500 italic">
            &gt; CLUSTER_SYNC: OK // ENGINE_READY
          </div>
        </footer>
      </div>

      <style jsx>{`
        .glass-hw {
          background: rgba(255, 255, 255, 0.015);
          border: 1px solid rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(25px);
          position: relative;
        }
        .glass-hw::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 2px; height: 100%;
          background: #ED1C24;
          pointer-events: none;
        }
        .btn-hw {
          background: rgba(237, 28, 36, 0.1);
          border: 1px solid #ED1C24;
          color: #ED1C24;
          padding: 0.5rem 1.2rem;
          font-size: 9px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.2em;
          cursor: pointer;
          transition: 0.3s;
          display: inline-block;
        }
        .btn-hw:hover {
          background: #ED1C24;
          color: white;
          box-shadow: 0 0 30px #ED1C24;
        }
      `}</style>
    </div>
  );
}

function TelemetryBar({ label, value, pct }: { label: string; value: string; pct: number }) {
  return (
    <div>
      <div className="flex justify-between font-mono text-[9px] mb-2">
        <span className="text-gray-500">{label}</span>
        <span className="text-white">{value}</span>
      </div>
      <div className="h-px bg-white/10 relative overflow-hidden">
        <div className="absolute inset-0 bg-red-600" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
