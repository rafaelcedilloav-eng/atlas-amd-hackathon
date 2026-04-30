"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as THREE from "three";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { atlasApi } from "@/services/api";
import { UploadModal } from "@/components/features/upload-modal";
import { XRayPanel } from "@/components/features/xray-panel";
import { useAuditStore } from "@/store/audit-store";

const NAV_LINKS = [
  { href: "/dashboard",    label: "Dashboard_Overview"  },
  { href: "/audits",       label: "Forensic_Archive"    },
  { href: "/analytics",    label: "Analytics_Vault"     },
  { href: "/hardware",     label: "Orchestration_Node"  },
  { href: "/intelligence", label: "Global_Intelligence" },
];

const TICKER = [
  { label: "BTC",     value: "64,291.20", dir: "▲", cls: "text-green-500" },
  { label: "VIX",     value: "14.22 %",   dir: "▼", cls: "text-red-500"   },
  { label: "USD/MXN", value: "16.82",     dir: "▬", cls: "text-white"     },
  { label: "AMD",     value: "158.42",    dir: "▲", cls: "text-green-500" },
];

export default function DashboardPage() {
  const canvasRef = useRef<HTMLDivElement>(null);
  const threeRef  = useRef<{ renderer?: THREE.WebGLRenderer; animId?: number }>({});
  const pathname  = usePathname();
  const [modalOpen, setModalOpen] = useState(false);

  const { data: stats } = useQuery({
    queryKey:        ["atlas-stats"],
    queryFn:         atlasApi.getStats,
    refetchInterval: 30_000,
  });

  const { data: recentAudits } = useQuery({
    queryKey:  ["dashboard-recent-audits"],
    queryFn:   () => atlasApi.getAudits(8),
    staleTime: 10_000,
  });

  const total     = stats?.total_audits    ?? 0;
  const fraud     = stats?.fraud_detected  ?? 0;
  const cleanDocs = Math.max(0, total - fraud);

  const { activeAuditId, phase, reset: resetAudit } = useAuditStore();

  useEffect(() => {
    if (!canvasRef.current) return;
    const scene    = new THREE.Scene();
    const camera   = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    canvasRef.current.appendChild(renderer.domElement);
    threeRef.current.renderer = renderer;

    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(2000 * 3);
    for (let i = 0; i < pPos.length; i++) pPos[i] = (Math.random() - 0.5) * 100;
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    const particles = new THREE.Points(
      pGeo,
      new THREE.PointsMaterial({ size: 0.05, color: 0xed1c24, transparent: true, opacity: 0.3 }),
    );
    scene.add(particles);

    const linePts: THREE.Vector3[] = [];
    for (let i = 0; i < 50; i++) {
      linePts.push(new THREE.Vector3((i - 25) * 2, Math.sin(i * 0.2) * 5, -10));
      linePts.push(new THREE.Vector3((i - 24) * 2, Math.sin((i + 1) * 0.2) * 5, -10));
    }
    const lines = new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(linePts),
      new THREE.LineBasicMaterial({ color: 0xed1c24, transparent: true, opacity: 0.1 }),
    );
    scene.add(lines);

    const core = new THREE.Mesh(
      new THREE.IcosahedronGeometry(4, 1),
      new THREE.MeshStandardMaterial({ color: 0xed1c24, wireframe: true, emissive: 0xed1c24, emissiveIntensity: 0.2 }),
    );
    scene.add(core);
    scene.add(new THREE.AmbientLight(0xffffff, 0.1));
    const pl = new THREE.PointLight(0xed1c24, 1, 50);
    pl.position.set(5, 5, 5);
    scene.add(pl);
    camera.position.z = 20;

    const clock = new THREE.Clock();
    function animate() {
      threeRef.current.animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      core.rotation.y      += 0.005;
      particles.rotation.y += 0.0002;
      lines.position.y      = Math.sin(t * 0.5) * 2;
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
      if (canvasRef.current && renderer.domElement.parentNode === canvasRef.current) {
        canvasRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden text-white">
      <div ref={canvasRef} className="absolute inset-0 z-[1]" />

      <div
        className="absolute inset-0 z-10 grid gap-4 p-6"
        style={{ gridTemplateColumns: "280px 1fr 320px", gridTemplateRows: "60px 1fr 110px" }}
      >
        {/* Header */}
        <motion.header
          className="col-span-3 glass-mc flex justify-between items-center px-8"
          initial={{ opacity: 0, y: -18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
        >
          <div className="flex items-center gap-6">
            <h1 className="text-2xl font-black uppercase italic tracking-tighter relative overflow-hidden select-none">
              ATLAS <span className="text-white/20">CMD_CENTER</span>
              <span
                className="absolute inset-0 pointer-events-none"
                style={{
                  background: "linear-gradient(105deg, transparent 30%, rgba(237,28,36,0.55) 50%, transparent 70%)",
                  animation: "redSweep 3.2s ease-in-out infinite",
                }}
              />
            </h1>
            <div className="font-mono text-[8px] text-red-500 uppercase tracking-widest animate-pulse">
              ● Bulk_Queue_Active
            </div>
          </div>
          <Link
            href="/"
            className="text-[8px] font-black uppercase opacity-40 hover:opacity-100 transition-opacity tracking-widest"
          >
            ← EXIT
          </Link>
        </motion.header>

        {/* Left nav */}
        <motion.aside
          className="glass-mc flex flex-col"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.45, ease: "easeOut", delay: 0.08 }}
        >
          <nav className="flex-1 mt-6">
            {NAV_LINKS.map(({ href, label }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`block px-4 py-4 border-l-2 transition-all duration-300 text-[0.75rem] font-bold uppercase tracking-[0.1em] ${
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
          <div className="p-6 border-t border-white/5 bg-red-600/5 mt-auto">
            <div className="text-[8px] text-red-500 font-bold mb-1 uppercase tracking-widest">Core_Engine</div>
            <div className="text-[10px] font-black text-white">ATLAS_v2.5</div>
          </div>
        </motion.aside>

        {/* Center — X-Ray Forensic Reasoning Theater */}
        <motion.main
          className="glass-mc flex flex-col overflow-hidden"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: "easeOut", delay: 0.14 }}
        >
          <XRayPanel
            auditId={activeAuditId}
            phase={phase}
            onReset={resetAudit}
          />
        </motion.main>

        {/* Right: Integrity Gate */}
        <motion.aside
          className="glass-mc flex flex-col p-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.45, ease: "easeOut", delay: 0.08 }}
        >
          <h2 className="text-xs font-black uppercase italic text-red-500 mb-4 border-b border-red-500/20 pb-2 tracking-tighter">
            Integrity_Gate_Live
          </h2>
          <div className="flex-1 overflow-y-auto space-y-2">
            <BucketCard label="Clean_Docs"    value={cleanDocs} cls="text-white"      />
            <BucketCard label="Duplicated"    value={0}          cls="text-yellow-500" labelCls="text-yellow-500" />
            <BucketCard label="Blocked"       value={fraud}      cls="text-red-500"    labelCls="text-red-500" accent />
            <BucketCard label="Pending_Batch" value={0}          cls="text-white/30"   dimmed />
          </div>
        </motion.aside>

        {/* Footer */}
        <motion.footer
          className="col-span-3 grid grid-cols-2 gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut", delay: 0.2 }}
        >
          <div className="glass-mc p-4 flex items-center justify-between">
            <div className="flex gap-3">
              <button
                onClick={() => setModalOpen(true)}
                className="bg-red-600 text-white font-black uppercase tracking-[0.1em] text-[9px] px-4 py-2 rounded-sm transition-all hover:shadow-[0_0_30px_#ED1C24] hover:-translate-y-0.5"
              >
                Single
              </button>
              <button
                onClick={() => setModalOpen(true)}
                className="bg-transparent border border-white text-white font-black uppercase tracking-[0.1em] text-[9px] px-4 py-2 rounded-sm transition-all hover:bg-white hover:text-black"
              >
                Bulk_Queue
              </button>
            </div>
            <div className="flex gap-6 border-l border-white/10 pl-6">
              <div className="text-center">
                <div className="text-[7px] text-gray-500 uppercase">In_Queue</div>
                <div className="text-lg font-black font-mono text-yellow-500">00</div>
              </div>
              <div className="text-center">
                <div className="text-[7px] text-gray-500 uppercase">Batch_Done</div>
                <div className="text-lg font-black font-mono text-blue-400">
                  {String(total).padStart(2, "0")}
                </div>
              </div>
            </div>
          </div>

          <div className="glass-mc p-4 flex flex-col justify-center overflow-hidden">
            <div className="text-[8px] text-red-500 font-black uppercase mb-2 tracking-[0.3em]">
              Risk_Management_Telemetry
            </div>
            <div className="overflow-hidden">
              <div className="flex gap-8 font-mono text-[10px] whitespace-nowrap animate-[ticker_30s_linear_infinite]">
                {[...TICKER, ...TICKER].map((t, i) => (
                  <span key={i} className="text-white shrink-0">
                    {t.label}: <span className={t.cls}>{t.value} {t.dir}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </motion.footer>
      </div>

      <UploadModal open={modalOpen} onClose={() => setModalOpen(false)} />

      <style jsx>{`
        .glass-mc {
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(237, 28, 36, 0.15);
          backdrop-filter: blur(20px);
          position: relative;
          overflow: hidden;
        }
        .glass-mc::before {
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
        @keyframes redSweep {
          0%   { transform: translateX(-120%); }
          60%  { transform: translateX(120%); }
          100% { transform: translateX(120%); }
        }
      `}</style>
    </div>
  );
}

function BucketCard({
  label, value, cls, labelCls, accent, dimmed,
}: {
  label: string; value: number; cls: string; labelCls?: string; accent?: boolean; dimmed?: boolean;
}) {
  return (
    <div
      className={`p-3 border bg-white/[0.01] ${accent ? "border-red-500/30" : "border-white/5"} ${dimmed ? "opacity-30" : ""}`}
    >
      <div className={`text-[8px] uppercase mb-1 ${labelCls ?? "text-gray-500"}`}>{label}</div>
      <div className={`text-xl font-black ${cls}`}>{String(value).padStart(2, "0")}</div>
    </div>
  );
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60)  return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60)  return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24)  return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}
