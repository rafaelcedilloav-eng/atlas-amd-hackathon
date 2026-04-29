"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import * as THREE from "three";
import gsap from "gsap";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { atlasApi } from "@/services/api";
import type { AuditListItem, AtlasAuditRow, HumanDecision } from "@/types/atlas";

const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"] as const;

function severityColor(s: string | null): string {
  if (s === "CRITICAL") return "text-red-500";
  if (s === "HIGH")     return "text-orange-500";
  if (s === "MEDIUM")   return "text-yellow-500";
  if (s === "LOW")      return "text-green-400";
  return "text-gray-400";
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

export default function ArchivePage() {
  const canvasRef  = useRef<HTMLDivElement>(null);
  const threeRef   = useRef<{
    renderer?: THREE.WebGLRenderer;
    animId?:   number;
    camera?:   THREE.PerspectiveCamera;
    nodes:     THREE.Mesh[];
  }>({ nodes: [] });
  const mouseRef   = useRef({ x: 0, y: 0 });
  const queryClient = useQueryClient();

  const [search,         setSearch]         = useState("");
  const [dSearch,        setDSearch]        = useState("");
  const [severity,       setSeverity]       = useState("");
  const [selectedId,     setSelectedId]     = useState<string | null>(null);
  const [decisionState,  setDecisionState]  = useState<"idle" | "loading" | "done">("idle");

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  const { data: auditsData, isLoading } = useQuery({
    queryKey:        ["audits", dSearch, severity],
    queryFn:         () => atlasApi.getAudits(50, dSearch || undefined, severity || undefined),
    refetchInterval: 30_000,
  });

  const { data: detail } = useQuery({
    queryKey: ["audit-detail", selectedId],
    queryFn:  () => atlasApi.getResult(selectedId!),
    enabled:  !!selectedId,
  });

  const audits = auditsData?.audits ?? [];

  // Three.js 30 rotating cubes + mouse tracking
  useEffect(() => {
    if (!canvasRef.current) return;
    const scene    = new THREE.Scene();
    const camera   = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    canvasRef.current.appendChild(renderer.domElement);
    threeRef.current.renderer = renderer;
    threeRef.current.camera   = camera;

    const nodes: THREE.Mesh[] = [];
    for (let i = 0; i < 30; i++) {
      const isCrit = Math.random() > 0.6;
      const mesh   = new THREE.Mesh(
        new THREE.BoxGeometry(1.2, 1.2, 1.2),
        new THREE.MeshStandardMaterial({
          color:            isCrit ? 0xed1c24 : 0x444444,
          wireframe:        true,
          emissive:         isCrit ? 0xed1c24 : 0x000000,
          emissiveIntensity: 0.5,
        }),
      );
      mesh.position.set(
        (Math.random() - 0.5) * 30,
        (Math.random() - 0.5) * 25,
        (Math.random() - 0.5) * 20,
      );
      scene.add(mesh);
      nodes.push(mesh);
    }
    threeRef.current.nodes = nodes;

    scene.add(new THREE.AmbientLight(0xffffff, 0.1));
    const pl = new THREE.PointLight(0xed1c24, 2, 120);
    pl.position.set(10, 10, 10);
    scene.add(pl);
    camera.position.z = 28;

    const clock = new THREE.Clock();
    function animate() {
      threeRef.current.animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      nodes.forEach((n, i) => {
        n.rotation.y    += 0.005;
        n.position.y    += Math.sin(t + i) * 0.003;
      });
      camera.position.x += (mouseRef.current.x * 6 - camera.position.x) * 0.05;
      camera.position.y += (mouseRef.current.y * 4 - camera.position.y) * 0.05;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
    }
    animate();

    const onMove = (e: MouseEvent) => {
      mouseRef.current.x = (e.clientX / window.innerWidth) * 2 - 1;
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

  const selectAudit = useCallback((audit: AuditListItem, idx: number) => {
    setSelectedId(audit.doc_id);
    setDecisionState("idle");
    // Zoom camera to nearest node
    const nodes = threeRef.current.nodes;
    if (nodes.length > 0 && threeRef.current.camera) {
      const target = nodes[idx % nodes.length].position;
      gsap.to(threeRef.current.camera.position, {
        x: target.x * 0.8, y: target.y * 0.8, z: target.z + 12,
        duration: 1.5, ease: "power3.inOut",
      });
    }
  }, []);

  const closeDetail = () => {
    setSelectedId(null);
    if (threeRef.current.camera) {
      gsap.to(threeRef.current.camera.position, { x: 0, y: 0, z: 28, duration: 1.5, ease: "expo.out" });
    }
  };

  const submitDecision = async (decision: HumanDecision) => {
    if (!selectedId || !decision) return;
    setDecisionState("loading");
    try {
      await atlasApi.submitDecision(selectedId, decision);
      setDecisionState("done");
      queryClient.invalidateQueries({ queryKey: ["audits"] });
      queryClient.invalidateQueries({ queryKey: ["audit-detail", selectedId] });
    } catch {
      setDecisionState("idle");
    }
  };

  const selectedAuditMeta = audits.find((a) => a.doc_id === selectedId);
  const reasoning   = detail?.result_json?.reasoning;
  const explanation = detail?.result_json?.explanation;
  const vision      = detail?.result_json?.vision;

  const vendorName = selectedAuditMeta?.vendor_name
    ?? (vision?.extracted_fields?.vendor_name?.value as string | null)
    ?? "UNKNOWN_ENTITY";

  const amountRaw = vision?.extracted_fields?.total_amount?.value
    ?? vision?.extracted_fields?.amount?.value;
  const amount = amountRaw != null ? `$${Number(amountRaw).toLocaleString("en-US")}` : "—";

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden text-white">
      <div ref={canvasRef} className="absolute inset-0 z-[1]" />

      <div className="absolute inset-0 z-10 flex flex-col p-10">
        {/* Header */}
        <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-4xl font-black uppercase italic tracking-tighter">
              FORENSIC<span className="text-white/20">_ARCHIVE</span>
            </h1>
            <div className="font-mono text-[10px] mt-1 opacity-50 uppercase tracking-widest">
              Neural_Vault // SEARCH_MODE_ACTIVE
            </div>
          </div>

          {/* Search bar */}
          <div className="relative w-[450px]">
            <svg
              className="absolute left-4 top-1/2 -translate-y-1/2 opacity-30 pointer-events-none"
              width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Document, Company or Country..."
              className="w-full bg-white/[0.03] border border-white/10 py-3 pl-12 pr-5 text-[11px] font-mono text-white placeholder:text-white/30 focus:outline-none focus:border-red-600 focus:shadow-[0_0_15px_rgba(237,28,36,0.2)] focus:bg-red-600/[0.05] transition-all"
            />
          </div>

          <div className="flex gap-4">
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="glass-ar py-2 px-4 text-[10px] font-bold uppercase tracking-widest bg-transparent text-white focus:outline-none cursor-pointer"
            >
              <option value="">All_Severity</option>
              {SEVERITIES.map((s) => (
                <option key={s} value={s} className="bg-black">{s}</option>
              ))}
            </select>
            <Link
              href="/dashboard"
              className="glass-ar py-2 px-6 text-[10px] font-bold uppercase tracking-widest hover:bg-red-600 transition-colors"
            >
              ← Mission_Control
            </Link>
          </div>
        </header>

        {/* Body */}
        <div className="flex-1 grid grid-cols-12 gap-10 overflow-hidden min-h-0">
          {/* Left: audit list */}
          <aside className="col-span-3 overflow-y-auto pr-2 custom-scroll">
            {isLoading ? (
              <div className="text-center font-mono text-[10px] text-gray-500 uppercase tracking-widest pt-10 animate-pulse">
                Loading_Records...
              </div>
            ) : audits.length === 0 ? (
              <div className="text-center font-mono text-[10px] text-gray-600 uppercase tracking-widest pt-10">
                No_Records_Found
              </div>
            ) : (
              audits.map((audit, i) => (
                <div
                  key={audit.doc_id}
                  onClick={() => selectAudit(audit, i)}
                  className={`cursor-pointer transition-all duration-300 border-l-2 p-5 mb-4 glass-ar ${
                    selectedId === audit.doc_id
                      ? "bg-red-600/5 border-l-red-600"
                      : "border-l-transparent hover:bg-red-600/5 hover:border-l-red-600 hover:translate-x-1.5"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-[11px] font-black tracking-tighter uppercase">
                      {audit.vendor_name ?? audit.doc_id.slice(0, 12).toUpperCase()}
                    </span>
                    <span className={`text-[8px] font-mono font-bold ${severityColor(audit.severity)}`}>
                      {audit.severity ?? "UNKNOWN"}
                    </span>
                  </div>
                  <div className="text-[9px] text-gray-500 mt-1 tracking-widest font-bold uppercase">
                    {audit.fraud_type ?? "NO_TRAP"} // {fmtDate(audit.created_at)}
                  </div>
                </div>
              ))
            )}
          </aside>

          {/* Center: analysis panel */}
          <main className="col-span-6 flex items-center justify-center relative">
            <div
              className={`glass-ar p-16 w-full max-w-[850px] max-h-[82vh] overflow-y-auto custom-scroll border-white/5 transition-all duration-700 ${
                selectedId ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"
              }`}
            >
              <div className="text-[10px] text-gray-500 uppercase mb-8 tracking-[0.4em] text-center">
                Neural_Forensic_Deep_Analysis
              </div>

              {detail ? (
                <>
                  {/* Summary */}
                  <div className="border-l border-white/10 pl-10 mb-14">
                    <div className="text-[12px] text-red-500 font-black uppercase mb-4 tracking-tighter">
                      Case_Detection_Summary
                    </div>
                    <p className="text-lg text-gray-200 leading-relaxed italic font-light">
                      &ldquo;{explanation?.explanation?.summary ?? "Analysis in progress..."}&rdquo;
                    </p>
                  </div>

                  {/* Reasoning chain */}
                  {reasoning?.reasoning_chain && reasoning.reasoning_chain.length > 0 && (
                    <div className="border-l border-blue-500/30 pl-10 mb-14">
                      <div className="text-[12px] text-blue-500 font-black uppercase mb-4 tracking-tighter">
                        AI_Reasoning_Chain
                      </div>
                      <div className="space-y-6 font-mono text-[11px]">
                        {reasoning.reasoning_chain.map((step, i) => (
                          <div key={i} className="flex gap-4">
                            <span className={`font-bold ${i === reasoning.reasoning_chain.length - 1 && reasoning.trap_severity !== "NONE" ? "text-red-500" : "text-blue-500"}`}>
                              [{String(step.step).padStart(2, "0")}]
                            </span>
                            <span className="text-gray-400 leading-relaxed">{step.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Full report link */}
                  <div className="text-center mt-4">
                    <Link
                      href={`/audits/${selectedId}`}
                      className="inline-block text-[9px] font-black uppercase tracking-[0.2em] border border-red-600/30 text-red-500 px-6 py-2 hover:bg-red-600 hover:text-white hover:shadow-[0_0_30px_#ED1C24] transition-all"
                    >
                      VIEW_FULL_REPORT →
                    </Link>
                  </div>
                </>
              ) : (
                <div className="text-center font-mono text-[10px] text-gray-600 animate-pulse uppercase tracking-widest">
                  Loading_Analysis...
                </div>
              )}
            </div>
          </main>

          {/* Right: operational panel */}
          <aside className="col-span-3 flex flex-col justify-end items-end">
            <div
              className={`glass-ar w-full p-10 border-white/10 transition-all duration-700 ${
                selectedId ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10 pointer-events-none"
              }`}
            >
              <div className="text-[10px] text-gray-500 uppercase mb-8 tracking-widest">
                Operational_Core
              </div>

              <div className="space-y-8 mb-12">
                <div>
                  <div className="text-[9px] text-gray-500 uppercase mb-2">Subject_Identity</div>
                  <div className="text-sm font-black text-white uppercase leading-tight">
                    {vendorName}
                  </div>
                  <div className="font-mono text-[10px] text-red-500 mt-2">
                    ID: {selectedId?.slice(0, 20)}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <div className="text-[9px] text-gray-500 uppercase mb-2">Total_Value</div>
                    <div className="text-lg font-black text-white">{amount}</div>
                  </div>
                  <div>
                    <div className="text-[9px] text-gray-500 uppercase mb-2">Severity</div>
                    <div className={`text-lg font-black ${severityColor(selectedAuditMeta?.severity ?? null)}`}>
                      {selectedAuditMeta?.severity ?? "—"}
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-[9px] text-gray-500 uppercase mb-2">Timestamp</div>
                  <div className="text-xs font-bold text-gray-400 font-mono">
                    {selectedAuditMeta ? fmtDate(selectedAuditMeta.created_at) : "—"}
                  </div>
                </div>
              </div>

              <div className="border-t border-white/10 pt-8">
                <div className="text-[10px] text-white/40 font-black uppercase mb-6 tracking-[0.3em]">
                  Decision_Protocol
                </div>
                {decisionState === "done" ? (
                  <div className="text-center font-mono text-[10px] text-green-400 uppercase tracking-widest py-4 animate-pulse">
                    ✓ Decision_Recorded
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-3">
                    <button
                      disabled={decisionState === "loading"}
                      onClick={() => submitDecision("APPROVE")}
                      className="py-3 bg-green-600/10 border border-green-600/30 text-green-500 text-[9px] font-black uppercase hover:bg-green-600 hover:text-white transition-all disabled:opacity-40"
                    >
                      APPROVE_DOCUMENT
                    </button>
                    <button
                      disabled={decisionState === "loading"}
                      onClick={() => submitDecision("REQUEST_MORE_INFO")}
                      className="py-3 bg-yellow-600/10 border border-yellow-600/30 text-yellow-500 text-[9px] font-black uppercase hover:bg-yellow-600 hover:text-white transition-all disabled:opacity-40"
                    >
                      FLAG_FOR_REVIEW
                    </button>
                    <button
                      disabled={decisionState === "loading"}
                      onClick={() => submitDecision("REJECT")}
                      className="py-3 bg-red-600/10 border border-red-600/30 text-red-500 text-[9px] font-black uppercase hover:bg-red-600 hover:text-white transition-all disabled:opacity-40"
                    >
                      BLOCK_VENDOR_ID
                    </button>
                  </div>
                )}
                <button
                  onClick={closeDetail}
                  className="w-full mt-6 py-2 border border-white/5 text-gray-600 text-[8px] font-bold uppercase hover:text-white transition-all"
                >
                  CLOSE_FILE_VIEW
                </button>
              </div>
            </div>
          </aside>
        </div>
      </div>

      <style jsx>{`
        .glass-ar {
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(25px);
          position: relative;
        }
        .glass-ar::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 2px; height: 100%;
          background: #ED1C24;
          pointer-events: none;
        }
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #ED1C24; border-radius: 2px; }
      `}</style>
    </div>
  );
}
