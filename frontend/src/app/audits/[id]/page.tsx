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
} from "lucide-react";
import { formatDate } from "@/lib/utils";
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
        message={(error as Error)?.message || "No se encontró la auditoría"}
      />
    );
  }

  const result = audit.result_json;
  const currentDecision = audit.human_decision;

  return (
    <div className="p-10 space-y-10 max-w-7xl mx-auto">
      <header className="flex items-center gap-6">
        <button
          onClick={() => router.back()}
          className="w-12 h-12 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center hover:bg-white/10 transition-all active:scale-95"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-3xl font-black tracking-tighter uppercase truncate">
              {String(id).slice(0, 16)}…
            </h2>
            <SeverityBadge
              severity={(result?.explanation?.trap_severity as Severity) ?? "NONE"}
              className="text-sm px-3"
            />
          </div>
          <p className="text-white/40 font-mono text-sm truncate">
            {result?.pdf_path}
          </p>
        </div>
        <div className="text-right shrink-0">
          <span className="text-[10px] text-white/40 font-bold uppercase tracking-widest block">
            Auditado el
          </span>
          <p className="text-white/80 font-medium">{formatDate(audit.created_at)}</p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2 space-y-10">
          {/* Executive Summary */}
          <section className="bg-white/5 border border-white/10 rounded-3xl p-8 space-y-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
              <AlertOctagon className="w-32 h-32 text-white" />
            </div>
            <div className="space-y-2">
              <span className="text-[10px] text-blue-400 font-bold uppercase tracking-widest flex items-center gap-2">
                <Info className="w-3 h-3" /> Resumen Ejecutivo
              </span>
              <h3 className="text-2xl font-bold text-white/90">
                {result?.explanation?.explanation?.title ?? "Sin título"}
              </h3>
              <p className="text-lg text-white/70 leading-relaxed">
                {result?.explanation?.explanation?.summary ?? "Sin resumen disponible."}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-white/10">
              <div className="space-y-1">
                <span className="text-[10px] text-red-400 font-bold uppercase tracking-widest">
                  ¿Por qué es una trampa?
                </span>
                <p className="text-sm text-white/60">
                  {result?.explanation?.explanation?.why_its_a_trap ?? "—"}
                </p>
              </div>
              <div className="space-y-1">
                <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest">
                  Impacto Financiero
                </span>
                <p className="text-sm text-white/60">
                  {result?.explanation?.explanation?.financial_impact ?? "—"}
                </p>
              </div>
            </div>
          </section>

          {/* Reasoning Chain */}
          <section className="space-y-6">
            <h3 className="text-xl font-bold flex items-center gap-3">
              <Layers className="w-5 h-5 text-blue-500" />
              Cadena de Razonamiento Forense
            </h3>
            {result?.reasoning?.reasoning_chain?.length ? (
              <ReasoningChain steps={result.reasoning.reasoning_chain} />
            ) : (
              <div className="p-10 border-2 border-dashed border-white/5 rounded-3xl text-center">
                <p className="text-white/20 italic">
                  No hay datos de razonamiento disponibles.
                </p>
              </div>
            )}
          </section>

          {/* Validation Details */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4">
              <h4 className="text-sm font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Validación de Lógica
              </h4>
              <div className="space-y-3">
                <Row
                  label="Lógicamente Consistente"
                  value={result?.validation?.validation_result?.logically_sound ? "SÍ" : "NO"}
                  positive={result?.validation?.validation_result?.logically_sound}
                />
                <Row
                  label="Trampa Confirmada"
                  value={result?.validation?.validation_result?.trap_is_real ? "CONFIRMADA" : "DESCARTADA"}
                  positive={!result?.validation?.validation_result?.trap_is_real}
                />
                <Row
                  label="Verificación Matemática"
                  value={result?.validation?.validation_result?.math_verified === false ? "FALLA" : "PASA"}
                  positive={result?.validation?.validation_result?.math_verified !== false}
                />
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4">
              <h4 className="text-sm font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                Métricas del Sistema
              </h4>
              <div className="space-y-3">
                <Row
                  label="Tiempo Total"
                  value={`${result?.total_processing_time_ms ?? 0}ms`}
                />
                <Row
                  label="Estado Pipeline"
                  value={result?.status ?? "—"}
                />
                <Row
                  label="Modelo Base"
                  value={result?.reasoning?.model_used ?? "—"}
                  mono
                />
              </div>
            </div>
          </section>
        </div>

        {/* Sidebar */}
        <aside className="space-y-8">
          {/* Confidence */}
          <section className="bg-blue-600/5 border border-blue-600/20 rounded-3xl p-8 space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-blue-400">
              Puntaje de Confianza
            </h3>
            {result?.explanation?.confidence_breakdown ? (
              <ConfidenceRadar data={result.explanation.confidence_breakdown} />
            ) : (
              <p className="text-white/20 italic text-sm text-center">Sin datos</p>
            )}
          </section>

          {/* Extracted Fields */}
          {result?.vision?.extracted_fields &&
            Object.keys(result.vision.extracted_fields).length > 0 && (
              <section className="space-y-4">
                <h3 className="text-sm font-bold uppercase tracking-widest text-white/40">
                  Datos Extraídos (OCR)
                </h3>
                <div className="space-y-2">
                  {Object.entries(result.vision.extracted_fields).map(([key, field]) => (
                    <div
                      key={key}
                      className="flex justify-between items-center p-3 bg-white/5 border border-white/5 rounded-xl"
                    >
                      <span className="text-xs text-white/40 font-bold uppercase">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span className="text-sm font-medium text-white/90 truncate max-w-[140px]">
                        {String(field.value ?? "—")}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            )}

          {/* Human Decision */}
          <section className="bg-white/5 border border-white/10 rounded-3xl p-8 space-y-6">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-widest text-white/40">
                Decisión Humana
              </h3>
              {currentDecision && (
                <p className="mt-2 text-xs font-semibold text-blue-400">
                  Decisión registrada: {currentDecision}
                </p>
              )}
            </div>

            <div className="space-y-3">
              <DecisionButton
                label="Aprobar Documento"
                active={currentDecision === "APPROVE"}
                disabled={decidingPending}
                onClick={() => submitDecision("APPROVE")}
                variant="success"
                pending={decidingPending}
              />
              <DecisionButton
                label="Marcar como Fraude"
                active={currentDecision === "REJECT"}
                disabled={decidingPending}
                onClick={() => submitDecision("REJECT")}
                variant="danger"
                pending={decidingPending}
              />
              <DecisionButton
                label="Solicitar más Info"
                active={currentDecision === "REQUEST_MORE_INFO"}
                disabled={decidingPending}
                onClick={() => submitDecision("REQUEST_MORE_INFO")}
                variant="neutral"
                pending={decidingPending}
              />
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  positive,
  mono,
}: {
  label: string;
  value: string;
  positive?: boolean;
  mono?: boolean;
}) {
  const color =
    positive === undefined
      ? "text-white"
      : positive
      ? "text-emerald-400"
      : "text-red-400";

  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-white/60">{label}</span>
      <span className={`${color} font-semibold ${mono ? "font-mono text-xs" : ""} truncate max-w-[160px]`}>
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
    "w-full py-4 font-bold rounded-xl transition-all flex items-center justify-center gap-2 border";
  const styles = {
    success: active
      ? "bg-emerald-600 border-emerald-500 text-white shadow-lg shadow-emerald-500/20"
      : "bg-emerald-600/10 border-emerald-600/20 hover:bg-emerald-600/20 text-emerald-400",
    danger: active
      ? "bg-red-600 border-red-500 text-white shadow-lg shadow-red-500/20"
      : "bg-red-600/10 border-red-600/20 hover:bg-red-600/20 text-red-400",
    neutral: active
      ? "bg-white/20 border-white/20 text-white"
      : "bg-white/5 border-white/10 hover:bg-white/10 text-white/60",
  };

  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${styles[variant]} disabled:cursor-not-allowed disabled:opacity-60`}
    >
      {pending && active && <Loader2 className="w-4 h-4 animate-spin" />}
      {label}
    </motion.button>
  );
}

function LoadingSkeleton() {
  return (
    <div className="p-10 space-y-10 animate-pulse max-w-7xl mx-auto">
      <div className="h-20 bg-white/5 rounded-3xl w-full" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2 space-y-10">
          <div className="h-64 bg-white/5 rounded-3xl w-full" />
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-white/5 rounded-2xl w-full" />
            ))}
          </div>
        </div>
        <div className="h-[600px] bg-white/5 rounded-3xl w-full" />
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="h-screen flex flex-col items-center justify-center p-10 space-y-4 text-center">
      <XCircle className="w-16 h-16 text-red-500 mb-2" />
      <h2 className="text-3xl font-black tracking-tighter uppercase text-white">
        Error de Carga
      </h2>
      <p className="text-white/40 max-w-md">{message}</p>
      <button
        onClick={() => window.location.reload()}
        className="px-6 py-2 bg-white/10 rounded-lg font-bold hover:bg-white/20 transition-all"
      >
        Reintentar
      </button>
    </div>
  );
}
