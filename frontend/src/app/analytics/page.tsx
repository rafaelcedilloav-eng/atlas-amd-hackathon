"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as THREE from "three";
import gsap from "gsap";
import { useQuery } from "@tanstack/react-query";
import { Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from "chart.js";
import { atlasApi } from "@/services/api";

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip);

const FAILURES = [
  { id: 0, name: "Unregistered_Vendors", pct: "42%", color: "text-red-500"    },
  { id: 1, name: "Signature_Mismatch",   pct: "28%", color: "text-red-500"    },
  { id: 2, name: "Logical_Anomalies",    pct: "18%", color: "text-orange-500" },
  { id: 3, name: "Metadata_Spoofing",    pct: "12%", color: "text-yellow-500" },
];

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard_Overview" },
  { href: "/audits",    label: "Forensic_Archive"  },
  { href: "/analytics", label: "Analytics_Vault"   },
  { href: "/hardware",  label: "Orchestration_Node" },
];

const RADAR_DATA = {
  labels: ["Vision", "Logic", "Vendors", "Metadata", "Sigs", "Blocks"],
  datasets: [{
    label:           "Score",
    data:            [95, 40, 85, 60, 90, 30],
    backgroundColor: "rgba(237, 28, 36, 0.2)",
    borderColor:     "#ED1C24",
    borderWidth:     2,
    pointBackgroundColor: "#fff",
  }],
};

const RADAR_OPTIONS = {
  scales: {
    r: {
      angleLines: { color: "rgba(255,255,255,0.1)" },
      grid:       { color: "rgba(255,255,255,0.1)" },
      pointLabels:{ color: "#64748b", font: { size: 8 } },
      ticks:      { display: false },
    },
  },
  plugins: { legend: { display: false } },
};

export default function AnalyticsPage() {
  const canvasRef  = useRef<HTMLDivElement>(null);
  const threeRef   = useRef<{
    renderer?: THREE.WebGLRenderer;
    animId?:   number;
    camera?:   THREE.PerspectiveCamera;
    cubes:     THREE.Mesh[];
  }>({ cubes: [] });
  const mouseRef   = useRef({ x: 0, y: 0 });
  const mainUiRef  = useRef<HTMLDivElement>(null);
  const pathname   = usePathname();

  const [deepDive, setDeepDive] = useState<number | null>(null);

  const { data: stats } = useQuery({
    queryKey:        ["atlas-stats"],
    queryFn:         atlasApi.getStats,
    refetchInterval: 30_000,
  });
  const { data: auditsData } = useQuery({
    queryKey: ["audits", "", ""],
    queryFn:  () => atlasApi.getAudits(20),
  });

  const total  = stats?.total_audits   ?? 0;
  const fraud  = stats?.fraud_detected ?? 0;
  const clean  = Math.max(0, total - fraud);
  const audits = auditsData?.audits ?? [];

  // Three.js: grid + particles + triple icosahedra
  useEffect(() => {
    if (!canvasRef.current) return;
    const scene    = new THREE.Scene();
    const camera   = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    canvasRef.current.appendChild(renderer.domElement);
    threeRef.current.renderer = renderer;
    threeRef.current.camera   = camera;

    // Grid floor
    const grid = new THREE.GridHelper(300, 80, 0xed1c24, 0x111111);
    grid.position.y   = -15;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity     = 0.2;
    scene.add(grid);

    // Particles
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(12000 * 3);
    for (let i = 0; i < pPos.length; i++) pPos[i] = (Math.random() - 0.5) * 200;
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    const particles = new THREE.Points(
      pGeo,
      new THREE.PointsMaterial({ size: 0.08, color: 0xed1c24, transparent: true, opacity: 0.4, blending: THREE.AdditiveBlending }),
    );
    scene.add(particles);

    // Core group (3 icosahedra)
    const coreGroup   = new THREE.Group();
    const outerShell  = new THREE.Mesh(
      new THREE.IcosahedronGeometry(8, 2),
      new THREE.MeshStandardMaterial({ color: 0xed1c24, wireframe: true, transparent: true, opacity: 0.05, emissive: 0xed1c24, emissiveIntensity: 0.1 }),
    );
    const innerNodes  = new THREE.Mesh(
      new THREE.IcosahedronGeometry(5.5, 4),
      new THREE.MeshStandardMaterial({ color: 0xed1c24, wireframe: true, emissive: 0xed1c24, emissiveIntensity: 0.6, metalness: 1, roughness: 0 }),
    );
    const coreEnergy  = new THREE.Mesh(
      new THREE.IcosahedronGeometry(2, 0),
      new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 2, transparent: true, opacity: 0.8 }),
    );
    coreGroup.add(outerShell, innerNodes, coreEnergy);
    scene.add(coreGroup);

    // Failure cubes orbiting
    const cubes: THREE.Mesh[] = [];
    FAILURES.forEach((_, i) => {
      const cube = new THREE.Mesh(
        new THREE.BoxGeometry(1.5, 1.5, 1.5),
        new THREE.MeshStandardMaterial({ color: 0xed1c24, wireframe: true, emissive: 0xed1c24, emissiveIntensity: 1 }),
      );
      const angle = (i / FAILURES.length) * Math.PI * 2;
      cube.position.set(Math.cos(angle) * 15, Math.sin(angle) * 5, Math.sin(angle) * 15);
      scene.add(cube);
      cubes.push(cube);
    });
    threeRef.current.cubes = cubes;

    scene.add(new THREE.AmbientLight(0xffffff, 0.2));
    const pl = new THREE.PointLight(0xed1c24, 5, 150);
    pl.position.set(30, 30, 30);
    scene.add(pl);
    camera.position.z = 35;

    const clock = new THREE.Clock();
    function animate() {
      threeRef.current.animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      particles.rotation.y  += 0.0003;
      grid.position.z        = (t * 5) % 15;
      outerShell.rotation.y -= 0.005;
      innerNodes.rotation.y += 0.01;
      coreEnergy.scale.setScalar(1 + Math.sin(t * 4) * 0.2);
      coreGroup.position.y   = Math.sin(t) * 1.5;
      cubes.forEach((c, i) => {
        const angle = (i / cubes.length) * Math.PI * 2 + t * 0.2;
        c.position.x = Math.cos(angle) * 15;
        c.position.z = Math.sin(angle) * 15;
        c.rotation.y += 0.01;
      });
      camera.position.x += (mouseRef.current.x * 12 - camera.position.x) * 0.05;
      camera.position.y += (mouseRef.current.y * 8  - camera.position.y) * 0.05;
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

  const enterDeepDive = (index: number) => {
    setDeepDive(index);
    if (mainUiRef.current) mainUiRef.current.style.opacity = "0.1";
    const cubes = threeRef.current.cubes;
    if (cubes[index] && threeRef.current.camera) {
      const c = cubes[index].position;
      gsap.to(threeRef.current.camera.position, {
        x: c.x * 0.9, y: c.y, z: c.z * 0.9,
        duration: 1.5, ease: "power4.inOut",
      });
    }
  };

  const exitDeepDive = () => {
    setDeepDive(null);
    if (mainUiRef.current) mainUiRef.current.style.opacity = "1";
    if (threeRef.current.camera) {
      gsap.to(threeRef.current.camera.position, { x: 0, y: 0, z: 35, duration: 1.5, ease: "expo.out" });
    }
  };

  const conf    = stats?.avg_confidence_pct ?? 0;
  const latency = stats?.avg_processing_time_ms != null ? (stats.avg_processing_time_ms / 1000).toFixed(3) : "0.000";

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden text-white">
      <div ref={canvasRef} className="absolute inset-0 z-[1]" />

      {/* Main UI */}
      <div
        ref={mainUiRef}
        className="absolute inset-0 z-10 flex flex-col p-10 transition-opacity duration-700"
      >
        {/* Header */}
        <header className="flex justify-between items-start mb-8">
          <div className="flex items-center gap-8">
            <Link
              href="/dashboard"
              className="btn-av text-[10px]"
            >
              ← TERMINAL_EXIT
            </Link>
            <div>
              <h1 className="text-5xl font-black uppercase italic tracking-tighter">
                ATLAS<span className="text-red-600">_DASHBOARD</span>
              </h1>
              <div className="font-mono text-[10px] mt-2 text-white/50 tracking-[0.4em]">
                ROCm_INFRASTRUCTURE // MEGA_CORE_v2.5
              </div>
            </div>
          </div>
          <div className="glass-av p-4 flex gap-12 border-r-4 border-r-red-600">
            <div className="text-right">
              <div className="text-[8px] text-gray-500 uppercase font-black">Integrity_Gate</div>
              <div className="text-xs font-black text-white">ACTIVE</div>
            </div>
            <div className="text-right">
              <div className="text-[8px] text-gray-500 uppercase font-black">Detected_Anomalies</div>
              <div className="text-xs font-black text-red-500">{fraud.toLocaleString()}</div>
            </div>
          </div>
        </header>

        {/* Body */}
        <div className="flex-1 grid grid-cols-12 gap-8 relative min-h-0">
          {/* Left */}
          <div className="col-span-3 space-y-6 overflow-y-auto">
            <div className="glass-av p-6">
              <h3 className="text-[10px] font-black uppercase mb-4 text-red-500">Integrity_Buckets</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <span className="text-[9px] text-gray-500 font-bold uppercase">Clean_Docs</span>
                  <span className="text-2xl font-black italic">{clean}</span>
                </div>
                <div className="flex justify-between items-end">
                  <span className="text-[9px] text-yellow-500 font-bold uppercase">Duplicated</span>
                  <span className="text-2xl font-black italic text-yellow-500">00</span>
                </div>
                <div className="flex justify-between items-end border-b border-red-600/30 pb-2">
                  <span className="text-[9px] text-red-500 font-bold uppercase">Blocked_Vendors</span>
                  <span className="text-2xl font-black italic text-red-500">{String(fraud).padStart(2, "0")}</span>
                </div>
                <div className="flex justify-between items-end pt-2">
                  <span className="text-[9px] text-gray-500 font-bold uppercase">Avg_Confidence</span>
                  <span className="text-xl font-black text-white">{Math.round(conf)}%</span>
                </div>
              </div>
            </div>

            <div className="glass-av p-6">
              <h3 className="text-[10px] font-black uppercase mb-2 text-red-500">Forensic_Strength</h3>
              <div style={{ height: 260, marginTop: "1rem" }}>
                <Radar data={RADAR_DATA} options={RADAR_OPTIONS as any} />
              </div>
            </div>
          </div>

          {/* Center — Three.js shows through */}
          <div className="col-span-6 relative flex items-center justify-center">
            <div className="absolute bottom-20 text-center pointer-events-none opacity-20">
              <div className="font-mono text-[9px] uppercase tracking-[2.5em]">Neural_Inference_Topology</div>
            </div>
          </div>

          {/* Right */}
          <div className="col-span-3 space-y-6 overflow-y-auto">
            <div className="glass-av overflow-hidden">
              <div className="p-6 border-b border-white/5">
                <h3 className="text-[10px] font-black uppercase text-red-500 tracking-widest">
                  Top_Failure_Categories
                </h3>
              </div>
              {FAILURES.map((f) => (
                <div
                  key={f.id}
                  onClick={() => enterDeepDive(f.id)}
                  className="px-6 py-4 border-b border-white/5 flex justify-between items-center cursor-pointer transition-all hover:bg-red-600/10 hover:border-l-2 hover:border-l-red-600"
                >
                  <div>
                    <div className={`text-xs font-bold ${f.color}`}>{f.name}</div>
                    <div className="font-mono text-[9px] text-red-500">{f.pct} OF TOTAL</div>
                  </div>
                  <div className="text-[8px] border border-red-500 px-2 py-1 text-red-500 font-bold">
                    NODE_ACTIVE
                  </div>
                </div>
              ))}
            </div>

            <div className="glass-av p-6 bg-red-600/5 border-red-600/20">
              <div className="text-[9px] text-red-500 font-black uppercase mb-2 italic">● Live_Insight</div>
              <p className="text-[10px] text-white/50 leading-relaxed italic">
                &ldquo;Escalating priority on unregistered vendor nodes. MI300X Node_04 under heavy inference load.&rdquo;
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 flex justify-between items-end border-t border-white/5 pt-6">
          <div className="font-mono text-[9px] opacity-40 uppercase tracking-widest">
            AMD_INSTINCT // ATLAS_FORENSIC_ENGINE
          </div>
          <div className="flex gap-20">
            <div className="text-center">
              <div className="text-[8px] text-gray-500 uppercase">Throughput</div>
              <div className="text-sm font-black font-mono">4.2 PB/S</div>
            </div>
            <div className="text-center">
              <div className="text-[8px] text-gray-500 uppercase">Avg_Latency</div>
              <div className="text-sm font-black text-red-600 font-mono">{latency}s</div>
            </div>
          </div>
        </footer>
      </div>

      {/* Deep Dive Modal */}
      {deepDive !== null && (
        <div className="absolute z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] glass-av p-8 border-white/20 shadow-[0_0_100px_rgba(237,28,36,0.2)] transition-all">
          <div className="flex justify-between items-center mb-8 border-b border-white/5 pb-4">
            <h2 className="text-2xl font-black uppercase italic text-red-500">
              {FAILURES[deepDive].name}
            </h2>
            <button
              onClick={exitDeepDive}
              className="btn-av text-[8px] py-1"
            >
              CLOSE_VAULT ✕
            </button>
          </div>
          <div className="space-y-4">
            {audits.slice(0, 4).map((a) => (
              <Link
                key={a.doc_id}
                href={`/audits/${a.doc_id}`}
                className="block p-4 bg-white/5 border border-white/5 hover:border-red-500 transition-all font-mono text-[10px]"
              >
                &gt; {a.doc_id.slice(0, 32)} // ACCESS_FULL_LOG
              </Link>
            ))}
            {audits.length === 0 && (
              <div className="font-mono text-[10px] text-gray-500 text-center py-4">
                No_Records_Available
              </div>
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        .glass-av {
          background: rgba(255, 255, 255, 0.015);
          border: 1px solid rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(25px);
          position: relative;
        }
        .glass-av::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 3px; height: 100%;
          background: #ED1C24;
          pointer-events: none;
        }
        .btn-av {
          background: rgba(237, 28, 36, 0.1);
          border: 1px solid #ED1C24;
          color: #ED1C24;
          padding: 0.6rem 1.5rem;
          font-size: 10px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.2em;
          cursor: pointer;
          transition: 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          display: inline-block;
        }
        .btn-av:hover {
          background: #ED1C24;
          color: white;
          box-shadow: 0 0 30px #ED1C24;
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
}
