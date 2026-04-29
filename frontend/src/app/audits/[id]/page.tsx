"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { atlasApi } from "@/services/api";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { ReasoningChain } from "@/components/features/reasoning-chain";
import { ConfidenceRadar } from "@/components/features/confidence-radar";
import {
  ArrowLeft,
  FileText,
  Cpu,
  AlertOctagon,
  CheckCircle2,
  XCircle,
  Info,
  Layers,
  Loader2,
  Zap,
  Terminal,
  ShieldCheck,
} from "lucide-react";
import { formatDate, cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { HumanDecision, Severity } from "@/types/atlas";

export default function AuditDetails() {
  const { id } = useParams();
  const router = useRouter();
  const qc = useQueryClient();

  const { data: audit, isLoading, error } = useQuery({
    queryKey: ["audit", id],
    queryFn: () => atlasApi.getResult(id as string),
    enabled: !!id,
    refetchInterval: (query) => {
       const status = query.state.data?.result_json?.status;
       return status === "COMPLETE" || status === "FAILED" ? false : 5000;
    }
  });

  const { mutate: submitDecision, isPending: decidingPending } = useMutation({
    mutationFn: (decision: HumanDecision) =>
      atlasApi.submitDecision(id as string, decision),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["audit", id] });
      qc.invalidateQueries({ queryKey: ["recent-audits"] });
    },
  });

  if (isLoading) return <LoadingSkeleton />;
  if (error || !audit) {
    return (
      <ErrorState
        message={(error as Error)?.message || "Audit not found"}
      />
    );
  }

  const result = audit.result_json;
  const currentDecision = audit.human_decision;

  return (
    <div className="p-10 space-y-12 max-w-7xl mx-auto bg-amd-black min-h-screen relative overflow-hidden">
      {/* Background Accent */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-amd-red/5 blur-[150px] rounded-full pointer-events-none" />

      <header className="flex items-center gap-8 relative z-10">
        <button
          onClick={() => router.back()}
          className="w-12 h-12 bg-amd-gray-900 border border-amd-gray-800 rounded flex items-center justify-center hover:bg-amd-red hover:text-white transition-all active:scale-95 group shadow-lg"
        >
          <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-4 flex-wrap">
            <h2 className="text-4xl font-black tracking-tighter uppercase truncate text-white">
              ANALYSIS_<span className="text-amd-red">{String(id).slice(0, 12)}</span>
            </h2>
            <SeverityBadge
              severity={(result?.explanation?.trap_severity as Severity) ?? "NONE"}
              className="text-xs px-4 py-1"
            />
          </div>
          <div className="flex items-center gap-4 mt-2">
            <p className="text-amd-gray-500 font-mono text-xs uppercase tracking-widest truncate max-w-md">
              PATH://{result?.pdf_path}
            </p>
            <span className="w-1 h-1 bg-amd-gray-800 rounded-full" />
            <div className="flex items-center gap-1">
              <Cpu className="w-3 h-3 text-amd-red" />
              <span className="text-[10px] font-mono text-amd-red font-bold uppercase tracking-tighter">AMD_MI300X_INF</span>
            </div>
          </div>
        </div>
        <div className="text-right shrink-0 bg-amd-gray-950 p-4 border border-amd-gray-900 rounded">
          <span className="text-[10px] text-amd-gray-600 font-black uppercase tracking-[0.2em] block mb-1">
            TIMESTAMP
          </span>
          <p className="text-white font-mono text-xs font-bold">{formatDate(audit.created_at)}</p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 relative z-10">
        <div className="lg:col-span-2 space-y-12">
          {/* Executive Summary */}
          <section className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-10 space-y-8 relative overflow-hidden group shadow-2xl">
            <div className="absolute top-0 left-0 w-1 h-full bg-amd-red opacity-50 group-hover:opacity-100 transition-opacity" />
            
            <div className="space-y-4">
              <span className="text-[10px] text-amd-red font-black uppercase tracking-[0.3em] flex items-center gap-3">
                <Terminal className="w-4 h-4" /> FORENSIC_EXECUTIVE_REPORT
              </span>
              <h3 className="text-3xl font-black text-white uppercase tracking-tighter leading-tight">
                {result?.explanation?.explanation?.title ?? "NO_ANALYSIS_TITLE"}
              </h3>
              <p className="text-lg text-amd-gray-300 leading-relaxed font-medium">
                {result?.explanation?.explanation?.summary ?? "Awaiting DeepSeek-R1 summary..."}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-amd-gray-800">
              <div className="space-y-3">
                <span className="text-[10px] text-amd-red font-black uppercase tracking-widest flex items-center gap-2">
                   ANOMALY_REASON
                </span>
                <p className="text-sm text-amd-gray-400 leading-relaxed italic">
                  "{result?.explanation?.explanation?.why_its_a_trap ?? "—"}"
                </p>
              </div>
              <div className="space-y-3">
                <span className="text-[10px] text-accent-success font-black uppercase tracking-widest flex items-center gap-2">
                   FINANCIAL_IMPACT
                </span>
                <p className="text-sm text-amd-gray-400 leading-relaxed">
                  {result?.explanation?.explanation?.financial_impact ?? "—"}
                </p>
              </div>
            </div>
          </section>

          {/* Reasoning Chain */}
          <section className="space-y-6">
            <h3 className="text-xs font-mono font-bold text-amd-gray-500 uppercase tracking-[0.3em] flex items-center gap-4">
              <Layers className="w-4 h-4 text-amd-red" />
              DEEPSEEK_R1_REASONING_CHAIN
            </h3>
            {result?.reasoning?.reasoning_chain?.length ? (
              <ReasoningChain steps={result.reasoning.reasoning_chain} />
            ) : (
              <div className="p-16 border border-dashed border-amd-gray-800 rounded bg-amd-gray-950/50 text-center">
                <Loader2 className="w-8 h-8 text-amd-red animate-spin mx-auto mb-4" />
                <p className="text-amd-gray-600 font-mono text-[10px] uppercase tracking-widest">
                  Extracting_Logical_Conclusions...
                </p>
              </div>
            )}
          </section>

          {/* Validation Details */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-amd-gray-950 border border-amd-gray-800 rounded-lg p-8 space-y-6">
              <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-amd-gray-500 flex items-center gap-3">
                <CheckCircle2 className="w-4 h-4 text-accent-success" />
                INTEGRITY_VERIFICATION
              </h4>
              <div className="space-y-4">
                <Row
                  label="Logic_Consistency"
                  value={result?.validation?.validation_result?.logically_sound ? "PASSED" : "FAILED"}
                  positive={result?.validation?.validation_result?.logically_sound}
                  mono
                />
                <Row
                  label="Anomaly_Detection"
                  value={result?.validation?.validation_result?.trap_is_real ? "CONFIRMED" : "NEGATIVE"}
                  positive={!result?.validation?.validation_result?.trap_is_real}
                  mono
                />
                <Row
                  label="Math_Engine"
                  value={result?.validation?.validation_result?.math_verified === false ? "CRITICAL_ERROR" : "VERIFIED"}
                  positive={result?.validation?.validation_result?.math_verified !== false}
                  mono
                />
              </div>
            </div>

            <div className="bg-amd-gray-950 border border-amd-gray-800 rounded-lg p-8 space-y-6">
              <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-amd-gray-500 flex items-center gap-3">
                <Zap className="w-4 h-4 text-accent-data" />
                HARDWARE_METRICS
              </h4>
              <div className="space-y-4">
                <Row
                  label="Total_Latency"
                  value={`${result?.total_processing_time_ms ?? 0}ms`}
                  mono
                />
                <Row
                  label="Pipeline_Status"
                  value={result?.status ?? "—"}
                  mono
                />
                <Row
                  label="Compute_Unit"
                  value="AMD_INSTINCT_MI300X"
                  accentColor="text-amd-red"
                  mono
                />
              </div>
            </div>
          </section>
        </div>

        {/* Sidebar */}
        <aside className="space-y-10">
          {/* Confidence */}
          <section className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-10 space-y-8 shadow-2xl">
            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-amd-red text-center">
              AGENT_CONFIDENCE_MAP
            </h3>
            {result?.explanation?.confidence_breakdown ? (
              <ConfidenceRadar data={result.explanation.confidence_breakdown} />
            ) : (
              <div className="h-40 flex items-center justify-center">
                <p className="text-amd-gray-600 font-mono text-[10px] uppercase tracking-widest animate-pulse">
                  Generating_Visualization...
                </p>
              </div>
            )}
          </section>

          {/* Human Decision */}
          <section className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-10 space-y-8 relative overflow-hidden group shadow-2xl">
            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-20 transition-opacity">
              <ShieldCheck className="w-16 h-16 text-white" />
            </div>
            
            <div>
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-amd-gray-500">
                HUMAN_DECISION_PROTOCOL
              </h3>
              {currentDecision && (
                <div className="mt-3 flex items-center gap-2">
                  <div className="w-1 h-1 bg-accent-data rounded-full animate-pulse" />
                  <p className="text-[10px] font-mono font-bold text-accent-data uppercase">
                    CURRENT_STATUS: {currentDecision}
                  </p>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <DecisionButton
                label="APPROVE_DOCUMENT"
                active={currentDecision === "APPROVE"}
                disabled={decidingPending}
                onClick={() => submitDecision("APPROVE")}
                variant="success"
                pending={decidingPending}
              />
              <DecisionButton
                label="FLAG_AS_FRAUD"
                active={currentDecision === "REJECT"}
                disabled={decidingPending}
                onClick={() => submitDecision("REJECT")}
                variant="danger"
                pending={decidingPending}
              />
              <DecisionButton
                label="REQUEST_INFORMATION"
                active={currentDecision === "REQUEST_MORE_INFO"}
                disabled={decidingPending}
                onClick={() => submitDecision("REQUEST_MORE_INFO")}
                variant="neutral"
                pending={decidingPending}
              />
            </div>
          </section>
          
           {/* Extracted Fields */}
          {result?.vision?.extracted_fields &&
            Object.keys(result.vision.extracted_fields).length > 0 && (
              <section className="space-y-6">
                <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-amd-gray-500 px-2">
                  EXTRACTED_OCR_TELEMETRY
                </h3>
                <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                  {Object.entries(result.vision.extracted_fields).map(([key, field]) => (
                    <div
                      key={key}
                      className="flex justify-between items-center p-4 bg-amd-gray-950 border border-amd-gray-900 rounded group hover:border-amd-gray-700 transition-colors"
                    >
                      <span className="text-[10px] text-amd-gray-500 font-mono uppercase group-hover:text-amd-gray-300 transition-colors">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs font-mono font-bold text-white truncate max-w-[140px]">
                        {String(field.value ?? "—")}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            )}
        </aside>
      </div>
      
       {/* Rafael's Spark - Quote */}
       <footer className="pt-10 opacity-30 text-center">
          <p className="font-mono text-[9px] text-amd-gray-600 italic uppercase tracking-[0.2em]">
            "A system without oversight is just an automated opinion."
          </p>
       </footer>
    </div>
  );
}

function Row({
  label,
  value,
  positive,
  mono,
  accentColor,
}: {
  label: string;
  value: string;
  positive?: boolean;
  mono?: boolean;
  accentColor?: string;
}) {
  const color =
    accentColor || (
    positive === undefined
      ? "text-white"
      : positive
      ? "text-accent-success"
      : "text-amd-red");

  return (
    <div className="flex justify-between items-center border-b border-amd-gray-900 pb-2 group hover:border-amd-gray-700 transition-colors">
      <span className="text-[11px] font-mono text-amd-gray-500 uppercase tracking-tighter">{label}</span>
      <span className={cn(
        "font-bold truncate max-w-[160px]",
        color,
        mono ? "font-mono text-xs tracking-tighter" : "text-sm"
      )}>
        {value}
      </span>
    </div>
  );
}

function DecisionButton({
  label,
  active,
  disabled,
  onClick,
  variant,
  pending,
}: {
  label: string;
  active: boolean;
  disabled: boolean;
  onClick: () => void;
  variant: "success" | "danger" | "neutral";
  pending: boolean;
}) {
  const base =
    "w-full py-5 font-black text-[10px] uppercase tracking-[0.2em] rounded transition-all flex items-center justify-center gap-3 border shadow-sm";
  const styles = {
    success: active
      ? "bg-accent-success border-accent-success text-amd-black shadow-[0_0_20px_rgba(0,230,118,0.3)]"
      : "bg-accent-success/5 border-accent-success/20 hover:bg-accent-success/10 text-accent-success",
    danger: active
      ? "bg-amd-red border-amd-red text-white shadow-[0_0_20px_rgba(237,28,36,0.3)]"
      : "bg-amd-red/5 border-amd-red/20 hover:bg-amd-red/10 text-amd-red",
    neutral: active
      ? "bg-amd-gray-700 border-amd-gray-600 text-white shadow-xl"
      : "bg-amd-gray-950 border-amd-gray-800 hover:bg-amd-gray-900 text-amd-gray-500",
  };

  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      whileHover={{ y: -2 }}
      onClick={onClick}
      disabled={disabled}
      className={cn(base, styles[variant], "disabled:cursor-not-allowed disabled:opacity-30")}
    >
      {pending && active && <Loader2 className="w-4 h-4 animate-spin" />}
      {label}
    </motion.button>
  );
}

function LoadingSkeleton() {
  return (
    <div className="p-10 space-y-12 animate-pulse max-w-7xl mx-auto bg-amd-black min-h-screen">
      <div className="h-24 bg-amd-gray-900 rounded w-full border border-amd-gray-800" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        <div className="lg:col-span-2 space-y-12">
          <div className="h-80 bg-amd-gray-900 rounded-lg w-full border border-amd-gray-800" />
          <div className="space-y-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-40 bg-amd-gray-900 rounded-lg w-full border border-amd-gray-800" />
            ))}
          </div>
        </div>
        <div className="h-[700px] bg-amd-gray-900 rounded-lg w-full border border-amd-gray-800" />
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="h-screen bg-amd-black flex flex-col items-center justify-center p-10 space-y-6 text-center">
      <div className="w-20 h-20 bg-amd-red/10 border border-amd-red/20 rounded-full flex items-center justify-center mb-4">
        <XCircle className="w-10 h-10 text-amd-red" />
      </div>
      <h2 className="text-4xl font-black tracking-tighter uppercase text-white">
        SYSTEM_FAILURE
      </h2>
      <p className="text-amd-gray-500 font-mono text-sm max-w-md uppercase tracking-tight leading-relaxed">
        {message}
      </p>
      <div className="flex gap-3">
        <a
          href="/audits"
          className="px-8 py-4 bg-amd-gray-900 border border-amd-gray-800 text-white font-black text-xs uppercase tracking-widest rounded hover:bg-amd-gray-800 transition-all"
        >
          ← Back to Audits
        </a>
        <button
          onClick={() => window.location.reload()}
          className="px-8 py-4 bg-amd-red text-white font-black text-xs uppercase tracking-widest rounded hover:bg-amd-red-deep transition-all shadow-lg"
        >
          Retry
        </button>
      </div>
    </div>
  );
}
