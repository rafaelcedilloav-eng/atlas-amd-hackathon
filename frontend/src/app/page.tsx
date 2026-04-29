"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import * as THREE from "three";
import gsap from "gsap";

const AGENTS = [
  { name: "Vision_Agent",   logs: ["> Initializing_OCR", "> Mapping_Context_Z", "> Extracting_Metadata"] },
  { name: "Reasoning_Unit", logs: ["> Pattern_Match_v4",  "> Running_Cross_Ref",  "> Anomaly_Detected"]   },
  { name: "Integrity_Gate", logs: ["> Checking_Registry", "> Validating_Signature", "> INTEGRITY_FAILED"] },
  { name: "Explainer_AI",   logs: ["> Synthesizing_Report", "> Weighting_Severity", "> FINAL_VERDICT_READY"] },
];

export default function LandingPage() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const rainRef      = useRef<HTMLCanvasElement>(null);
  const threeRef     = useRef<{ core?: THREE.Mesh; renderer?: THREE.WebGLRenderer; animId?: number }>({});
  const mouseRef     = useRef({ x: 0, y: 0 });

  const [phase, setPhase]         = useState<"intro" | "running" | "done">("intro");
  const [agentName, setAgentName] = useState("Vision_Agent");
  const [progress, setProgress]   = useState(0);
  const [logs, setLogs]           = useState<string[]>([]);

  // Binary rain canvas
  useEffect(() => {
    const canvas = rainRef.current as HTMLCanvasElement;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let animId: number;
    let drops: number[] = [];

    function init() {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
      const cols = Math.floor(canvas.width / 14);
      drops = Array.from({ length: cols }, () => Math.random() * -100);
    }

    function draw() {
      ctx.fillStyle = "rgba(0,0,0,0.05)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = "14px 'JetBrains Mono', monospace";
      drops.forEach((y, i) => {
        const ch = Math.floor(Math.random() * 2).toString();
        const x  = i * 14;
        const py = y * 14;
        ctx.fillStyle = "#300000";
        ctx.fillText(ch, x, py);
        ctx.fillStyle = Math.random() > 0.9 ? "#ffffff" : "#ED1C24";
        ctx.fillText(ch, x, py);
        if (py > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      });
      animId = requestAnimationFrame(draw);
    }

    init();
    draw();
    window.addEventListener("resize", init);
    return () => { cancelAnimationFrame(animId); window.removeEventListener("resize", init); };
  }, []);

  // Three.js scene
  useEffect(() => {
    if (!containerRef.current) return;
    const scene    = new THREE.Scene();
    const camera   = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    containerRef.current.appendChild(renderer.domElement);
    threeRef.current.renderer = renderer;

    const coreGroup = new THREE.Group();
    const outer = new THREE.Mesh(
      new THREE.IcosahedronGeometry(2.5, 2),
      new THREE.MeshStandardMaterial({ color: 0xED1C24, wireframe: true, emissive: 0xED1C24, emissiveIntensity: 0.5, metalness: 1, roughness: 0 })
    );
    const inner = new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.5, 0),
      new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.2 })
    );
    coreGroup.add(outer, inner);
    scene.add(coreGroup);
    threeRef.current.core = outer;

    scene.add(new THREE.AmbientLight(0xffffff, 0.2));
    const pl = new THREE.PointLight(0xED1C24, 2, 100);
    pl.position.set(10, 10, 10);
    scene.add(pl);
    camera.position.z = 12;

    const clock = new THREE.Clock();
    function animate() {
      threeRef.current.animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      outer.rotation.y += 0.005;
      outer.scale.setScalar(1 + Math.sin(t * 2) * 0.05);
      camera.position.x += (mouseRef.current.x * 2 - camera.position.x) * 0.05;
      camera.position.y += (mouseRef.current.y * 2 - camera.position.y) * 0.05;
      camera.lookAt(0, 0, 0);
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
      if (containerRef.current && renderer.domElement.parentNode === containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  // Mouse tracking
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      mouseRef.current.x = (e.clientX / window.innerWidth)  *  2 - 1;
      mouseRef.current.y = (e.clientY / window.innerHeight) * -2 + 1;
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  async function runAuditSequence() {
    setPhase("running");
    setLogs([]);
    setProgress(0);

    for (let i = 0; i < AGENTS.length; i++) {
      const agent = AGENTS[i];
      setAgentName(agent.name);
      if (threeRef.current.core) {
        gsap.to(threeRef.current.core.rotation, { y: threeRef.current.core.rotation.y + Math.PI, duration: 1 });
      }
      for (const log of agent.logs) {
        setLogs((prev) => [log, ...prev]);
        await sleep(600);
      }
      const targetPct = ((i + 1) / AGENTS.length) * 100;
      await animateProgress(setProgress, targetPct);
    }

    setPhase("done");
    await sleep(800);
    router.push("/dashboard");
  }

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden">
      {/* Binary rain */}
      <canvas ref={rainRef} className="absolute inset-0 z-0 opacity-40" />
      {/* Three.js */}
      <div ref={containerRef} className="absolute inset-0 z-[1]" />

      {/* UI overlay */}
      <div className="absolute inset-0 z-10 flex flex-col p-10 pointer-events-none">
        {/* Header */}
        <header className="flex justify-between items-start pointer-events-auto">
          <div>
            <h1 className="text-5xl font-black uppercase italic tracking-tighter bg-gradient-to-r from-white via-gray-300 via-[#ED1C24] via-gray-300 to-white bg-[length:200%_auto] animate-[shimmer-liquid_5s_linear_infinite] bg-clip-text text-transparent drop-shadow-[0_0_12px_rgba(237,28,36,0.4)]"
              style={{ WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              ATLAS_FOR_AMD
            </h1>
            <div className="mt-2 font-mono text-[10px] text-white/60 tracking-[0.4em] uppercase">
              Neural_Forensics // MI300X_Accelerated
            </div>
          </div>
          <div className="glass-amd p-5 w-72 text-right border-r-4 border-r-red-600">
            <div className="text-[9px] text-gray-500 uppercase tracking-widest mb-1">System Integrity</div>
            <div className="text-xs font-black text-white">AMD_INSTINCT_MI300X // ACTIVE</div>
            <div className="mt-3 flex justify-end gap-1">
              {[1, 0.8, 0.4, 0.3].map((op, i) => (
                <div key={i} className="w-1 h-4 bg-red-600 animate-pulse" style={{ opacity: op }} />
              ))}
            </div>
          </div>
        </header>

        {/* Center */}
        <div className="flex-1 flex flex-col items-center justify-center pointer-events-auto">
          {phase === "intro" && (
            <div className="text-center">
              <div className="font-mono text-[10px] text-white/50 mb-6 tracking-[0.5em] uppercase">
                Initializing Analysis Theater...
              </div>
              <button
                onClick={runAuditSequence}
                className="border border-[#ED1C24] text-[#ED1C24] bg-[rgba(237,28,36,0.05)] px-10 py-4 font-black uppercase tracking-[0.2em] text-lg transition-all duration-300 hover:bg-[#ED1C24] hover:text-white hover:shadow-[0_0_50px_#ED1C24] hover:-translate-y-0.5"
              >
                SYSTEM ACCESS
              </button>
            </div>
          )}

          {(phase === "running" || phase === "done") && (
            <div className="glass-amd w-96 p-6 text-left">
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-black uppercase italic text-red-500">{agentName}</span>
                <span className="font-mono text-[10px] text-white">{Math.round(progress)}%</span>
              </div>
              <div className="h-px w-full bg-red-950 relative overflow-hidden">
                <div
                  className="absolute inset-0 bg-red-600 shadow-[0_0_10px_#ED1C24] transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="mt-4 font-mono text-[10px] h-16 overflow-hidden leading-relaxed text-gray-400">
                {logs.slice(0, 4).map((l, i) => <div key={i}>{l}</div>)}
              </div>
              {phase === "done" && (
                <div className="mt-3 text-center font-mono text-[10px] text-green-400 animate-pulse">
                  → NAVIGATING TO MISSION CONTROL...
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer stats */}
        <footer className="grid grid-cols-4 gap-6 pointer-events-auto">
          {[
            { label: "Confidence", value: "94.2", unit: "%" },
            { label: "VRAM Pool",  value: "192",  unit: "GB" },
            { label: "Latency",    value: "0.08", unit: "ms" },
            { label: "Threats",    value: "03",   unit: "",   accent: true },
          ].map((s) => (
            <div key={s.label} className={`glass-amd p-4 flex flex-col ${s.accent ? "border-r-4 border-r-red-600" : ""}`}>
              <div className={`text-[9px] uppercase mb-2 ${s.accent ? "text-red-500" : "text-gray-500"}`}>{s.label}</div>
              <div className={`text-2xl font-black ${s.accent ? "text-red-500" : "text-white"}`}>
                {s.value}
                {s.unit && <span className="text-xs text-red-500 ml-1">{s.unit}</span>}
              </div>
            </div>
          ))}
        </footer>
      </div>

      <style jsx>{`
        .glass-amd {
          background: rgba(255,255,255,0.02);
          border: 1px solid rgba(255,255,255,0.05);
          backdrop-filter: blur(20px);
          box-shadow: 0 0 40px rgba(0,0,0,0.8);
          position: relative;
        }
        .glass-amd::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 3px; height: 100%;
          background: linear-gradient(to bottom, #ED1C24, transparent);
        }
        @keyframes shimmer-liquid {
          0%   { background-position: -200% center; }
          100% { background-position:  200% center; }
        }
      `}</style>
    </div>
  );
}

function sleep(ms: number) {
  return new Promise<void>((r) => setTimeout(r, ms));
}

function animateProgress(setter: (v: number) => void, target: number): Promise<void> {
  return new Promise((resolve) => {
    const start   = Date.now();
    const duration = 1500;
    const from     = 0;

    function tick() {
      const elapsed = Date.now() - start;
      const t       = Math.min(elapsed / duration, 1);
      const eased   = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      setter(from + (target - from) * eased);
      if (t < 1) requestAnimationFrame(tick);
      else resolve();
    }
    tick();
  });
}
