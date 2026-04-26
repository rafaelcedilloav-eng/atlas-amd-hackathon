"use client";

import { useState } from "react";
import Link from "next/link";
import { Upload, FileText, Activity, AlertTriangle, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { UploadModal } from "@/components/features/upload-modal";
import { RiskChart } from "@/components/features/risk-chart";
import { useAtlasStats } from "@/hooks/useAtlasStats";
import { useRecentAudits } from "@/hooks/useRecentAudits";
import { formatDate } from "@/lib/utils";
import { Severity } from "@/types/atlas";

export default function Dashboard() {
  const [uploadOpen, setUploadOpen] = useState(false);
  const { data: stats, isLoading: statsLoading } = useAtlasStats();
  const { data: auditsData, isLoading: auditsLoading } = useRecentAudits(8);

  const recentAudits = auditsData?.audits ?? [];

  return (
    <>
      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />

      <div className="p-10 space-y-10">
        <header className="flex justify-between items-end">
          <div>
            <h2 className="text-4xl font-black tracking-tighter">Panel de Control</h2>
            <p className="text-white/40 font-medium">
              Resumen del estado de integridad documental.
            </p>
          </div>
          <button
            onClick={() => setUploadOpen(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-6 rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-blue-500/20 active:scale-95"
          >
            <Upload className="w-5 h-5" />
            Nueva Auditoría
          </button>
        </header>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard
            icon={<FileText className="text-blue-400" />}
            label="Auditorías Totales"
            value={statsLoading ? "—" : String(stats?.total_audits ?? 0)}
          />
          <StatCard
            icon={<AlertTriangle className="text-red-400" />}
            label="Fraudes Detectados"
            value={statsLoading ? "—" : String(stats?.fraud_detected ?? 0)}
          />
          <StatCard
            icon={<ShieldCheck className="text-emerald-400" />}
            label="Confianza Promedio"
            value={statsLoading ? "—" : `${stats?.avg_confidence_pct ?? 0}%`}
          />
          <StatCard
            icon={<Activity className="text-purple-400" />}
            label="Tiempo de Inferencia"
            value={statsLoading ? "—" : `${stats?.avg_processing_time_ms ?? 0}ms`}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Recent Activity */}
          <div className="lg:col-span-2 space-y-6">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-500" />
              Actividad Reciente
            </h3>

            <div className="bg-white/5 border border-white/10 rounded-2xl divide-y divide-white/10 overflow-hidden">
              {auditsLoading ? (
                [...Array(4)].map((_, i) => (
                  <div key={i} className="p-4 flex items-center gap-4 animate-pulse">
                    <div className="w-10 h-10 bg-white/5 rounded-lg shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 bg-white/5 rounded w-2/5" />
                      <div className="h-2 bg-white/5 rounded w-1/4" />
                    </div>
                    <div className="h-5 w-16 bg-white/5 rounded-full" />
                  </div>
                ))
              ) : recentAudits.length === 0 ? (
                <div className="p-12 text-center space-y-3">
                  <FileText className="w-8 h-8 text-white/10 mx-auto" />
                  <p className="text-white/20 italic text-sm">
                    Sin auditorías. Sube un documento para comenzar.
                  </p>
                  <button
                    onClick={() => setUploadOpen(true)}
                    className="text-blue-400 text-sm font-semibold hover:underline"
                  >
                    Subir ahora →
                  </button>
                </div>
              ) : (
                recentAudits.map((item, i) => (
                  <motion.div
                    key={item.doc_id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                  >
                    <Link
                      href={`/audits/${item.doc_id}`}
                      className="p-4 flex items-center justify-between hover:bg-white/5 transition-colors block"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center shrink-0">
                          <FileText className="w-5 h-5 text-white/40" />
                        </div>
                        <div>
                          <h4 className="font-bold text-white/90 font-mono text-sm">
                            {item.doc_id.slice(0, 14)}…
                          </h4>
                          <p className="text-xs text-white/40">
                            {item.fraud_type || "Sin tipo"} •{" "}
                            {item.fraud_classification || "Sin clasificar"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <SeverityBadge
                          severity={(item.severity as Severity) ?? "NONE"}
                        />
                        <span className="text-xs text-white/20 font-mono hidden lg:block">
                          {formatDate(item.created_at)}
                        </span>
                      </div>
                    </Link>
                  </motion.div>
                ))
              )}
            </div>
          </div>

          {/* Risk Distribution */}
          <div className="space-y-6">
            <h3 className="text-xl font-bold">Distribución de Riesgo</h3>
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 h-[300px]">
              {statsLoading ? (
                <div className="h-full flex items-center justify-center">
                  <p className="text-white/20 italic text-sm">Cargando...</p>
                </div>
              ) : stats ? (
                <RiskChart distribution={stats.distribution} />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <p className="text-white/20 italic text-sm">Sin datos</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="bg-white/5 border border-white/10 p-6 rounded-2xl space-y-2 hover:border-white/20 transition-all group">
      <div className="w-8 h-8 bg-white/5 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <div>
        <p className="text-[10px] text-white/40 font-bold uppercase tracking-widest">
          {label}
        </p>
        <p className="text-3xl font-black tracking-tighter text-white/90">{value}</p>
      </div>
    </div>
  );
}
