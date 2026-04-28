"use client";

import { useState } from "react";
import Link from "next/link";
import { Upload, FileText, Activity, AlertTriangle, ShieldCheck, Cpu } from "lucide-react";
import { motion } from "framer-motion";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { UploadModal } from "@/components/features/upload-modal";
import { RiskChart } from "@/components/features/risk-chart";
import { useAtlasStats } from "@/hooks/useAtlasStats";
import { useRecentAudits } from "@/hooks/useRecentAudits";
import { formatDate, cn } from "@/lib/utils";
import { Severity } from "@/types/atlas";

export default function Dashboard() {
  const [uploadOpen, setUploadOpen] = useState(false);
  const { data: stats, isLoading: statsLoading } = useAtlasStats();
  const { data: auditsData, isLoading: auditsLoading } = useRecentAudits(8);

  const recentAudits = auditsData?.audits ?? [];

  return (
    <>
      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />

      <div className="p-10 space-y-12 bg-amd-black min-h-screen relative overflow-hidden">
        {/* Subtle Background Glow */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-amd-red/5 blur-[120px] rounded-full pointer-events-none" />

        <header className="flex justify-between items-end relative z-10">
          <div>
            <h2 className="text-5xl font-black tracking-tighter uppercase text-white">
              <span className="text-amd-red">ATLAS</span> SYSTEM
            </h2>
            <p className="text-amd-gray-500 font-mono text-xs uppercase tracking-[0.3em] mt-2">
              Deep_Auditor // Forensic_Analysis_Unit
            </p>
          </div>
          <button
            onClick={() => setUploadOpen(true)}
            className="bg-amd-red hover:bg-amd-red-deep text-white font-black py-4 px-8 rounded flex items-center gap-3 transition-all shadow-[0_0_25px_rgba(237,28,36,0.2)] hover:shadow-[0_0_40px_rgba(237,28,36,0.4)] active:scale-95 uppercase text-xs tracking-widest"
          >
            <Upload className="w-5 h-5" />
            New Audit
          </button>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10">
          <StatCard
            icon={<FileText className="text-white" />}
            label="Total Audits"
            value={statsLoading ? "—" : String(stats?.total_audits ?? 0)}
            subValue="DOC_PROCESSED"
          />
          <StatCard
            icon={<AlertTriangle className="text-amd-red" />}
            label="Fraud Detected"
            value={statsLoading ? "—" : String(stats?.fraud_detected ?? 0)}
            subValue="THREATS_IDENTIFIED"
            accent
          />
          <StatCard
            icon={<ShieldCheck className="text-accent-success" />}
            label="Avg. Confidence"
            value={statsLoading ? "—" : `${stats?.avg_confidence_pct ?? 0}%`}
            subValue="VALIDATION_SCORE"
          />
          <StatCard
            icon={<Cpu className="text-accent-data" />}
            label="Inference Latency"
            value={statsLoading ? "—" : `${((stats?.avg_processing_time_ms ?? 0) / 1000).toFixed(1)}s`}
            subValue="AMD_MI300X_GFLOPS"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 relative z-10">
          {/* Recent Activity */}
          <div className="lg:col-span-2 space-y-6">
            <h3 className="text-xs font-mono font-bold text-amd-gray-500 uppercase tracking-widest flex items-center gap-3">
              <Activity className="w-4 h-4 text-amd-red" />
              Recent_Activity_Monitor
            </h3>

            <div className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg divide-y divide-amd-gray-800 overflow-hidden shadow-2xl">
              {auditsLoading ? (
                [...Array(4)].map((_, i) => (
                  <div key={i} className="p-6 flex items-center gap-6 animate-pulse">
                    <div className="w-12 h-12 bg-amd-gray-800 rounded shrink-0" />
                    <div className="flex-1 space-y-3">
                      <div className="h-4 bg-amd-gray-800 rounded w-2/5" />
                      <div className="h-3 bg-amd-gray-800 rounded w-1/4" />
                    </div>
                    <div className="h-6 w-20 bg-amd-gray-800 rounded" />
                  </div>
                ))
              ) : recentAudits.length === 0 ? (
                <div className="p-20 text-center space-y-4">
                  <div className="w-16 h-16 bg-amd-gray-950 rounded-full flex items-center justify-center mx-auto border border-amd-gray-800">
                    <FileText className="w-8 h-8 text-amd-gray-700" />
                  </div>
                  <p className="text-amd-gray-500 font-mono text-xs uppercase tracking-widest">
                    Awaiting_Input_Data
                  </p>
                  <button
                    onClick={() => setUploadOpen(true)}
                    className="text-amd-red text-xs font-bold uppercase tracking-widest hover:underline"
                  >
                    Start Inference →
                  </button>
                </div>
              ) : (
                recentAudits.map((item, i) => (
                  <motion.div
                    key={item.doc_id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <Link
                      href={`/audits/${item.doc_id}`}
                      className="p-6 flex items-center justify-between hover:bg-amd-gray-950 transition-all group relative overflow-hidden"
                    >
                      <div className="absolute left-0 top-0 bottom-0 w-0 bg-amd-red group-hover:w-1 transition-all" />
                      
                      <div className="flex items-center gap-6">
                        <div className="w-12 h-12 bg-amd-gray-950 border border-amd-gray-800 rounded flex items-center justify-center shrink-0 group-hover:border-amd-red/30 transition-colors">
                          <FileText className="w-6 h-6 text-amd-gray-500 group-hover:text-amd-red" />
                        </div>
                        <div>
                          <h4 className="font-mono font-bold text-white text-sm tracking-tighter uppercase group-hover:text-amd-red transition-colors">
                            HEX_{item.doc_id.slice(0, 16)}
                          </h4>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] font-mono text-amd-gray-500 uppercase">
                              {item.fraud_type || "NO_TRAP"}
                            </span>
                            <span className="w-1 h-1 bg-amd-gray-800 rounded-full" />
                            <span className="text-[10px] font-mono text-amd-red uppercase font-bold">
                              {item.fraud_classification || "UNCLASSIFIED"}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-8">
                        <SeverityBadge
                          severity={(item.severity as Severity) ?? "NONE"}
                        />
                        <div className="text-right hidden lg:block">
                          <p className="text-[10px] font-mono text-white/90 uppercase font-bold">
                            TIMESTAMP
                          </p>
                          <p className="text-[10px] font-mono text-amd-gray-500 uppercase">
                            {formatDate(item.created_at)}
                          </p>
                        </div>
                      </div>
                    </Link>
                  </motion.div>
                ))
              )}
            </div>
          </div>

          {/* Risk Distribution */}
          <div className="space-y-6">
             <h3 className="text-xs font-mono font-bold text-amd-gray-500 uppercase tracking-widest flex items-center gap-3">
              Risk_Visualization
            </h3>
            <div className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-8 h-[380px] shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <ShieldCheck className="w-24 h-24 text-amd-red" />
              </div>
              
              {statsLoading ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center space-y-4">
                    <Activity className="w-8 h-8 text-amd-red animate-pulse mx-auto" />
                    <p className="text-amd-gray-600 font-mono text-[10px] uppercase tracking-widest">Computing_Distribution</p>
                  </div>
                </div>
              ) : stats ? (
                <RiskChart distribution={stats.distribution} />
              ) : (
                <div className="h-full flex items-center justify-center">
                   <p className="text-amd-gray-600 font-mono text-[10px] uppercase tracking-widest text-center leading-relaxed">
                    No Telemetry Data<br/>Available
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Rafael's Spark - Bottom bar */}
        <footer className="pt-20 pb-10 flex justify-between items-center opacity-20 hover:opacity-100 transition-opacity">
          <p className="font-mono text-[9px] text-amd-gray-500 uppercase tracking-[0.4em]">
            AMD // ROCM_6.16 // DEEPSEEK_R1_ATLAS_V1
          </p>
          <p className="font-mono text-[9px] text-amd-gray-500 italic uppercase">
            "Intelligence is the result of precision at scale."
          </p>
        </footer>
      </div>
    </>
  );
}

function StatCard({
  icon,
  label,
  value,
  subValue,
  accent = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subValue?: string;
  accent?: boolean;
}) {
  return (
    <div className={cn(
      "p-6 rounded-lg space-y-4 transition-all duration-300 relative overflow-hidden group border",
      accent 
        ? "bg-amd-red/5 border-amd-red/20 hover:border-amd-red/50" 
        : "bg-amd-gray-900 border-amd-gray-800 hover:border-amd-gray-700"
    )}>
      {/* Background Glow on Hover */}
      <div className={cn(
        "absolute -right-4 -top-4 w-16 h-16 rounded-full blur-2xl transition-opacity opacity-0 group-hover:opacity-20",
        accent ? "bg-amd-red" : "bg-white"
      )} />

      <div className={cn(
        "w-10 h-10 rounded flex items-center justify-center transition-transform group-hover:scale-110 duration-500",
        accent ? "bg-amd-red/20" : "bg-amd-gray-950 border border-amd-gray-800"
      )}>
        {icon}
      </div>
      
      <div>
        <div className="flex justify-between items-start">
          <p className="text-[10px] text-amd-gray-500 font-mono font-bold uppercase tracking-widest">
            {label}
          </p>
          {subValue && (
            <span className="text-[8px] font-mono text-amd-red/60 uppercase tracking-tighter">
              {subValue}
            </span>
          )}
        </div>
        <p className={cn(
          "text-4xl font-black tracking-tighter mt-1",
          accent ? "text-amd-red" : "text-white"
        )}>
          {value}
        </p>
      </div>
    </div>
  );
}
