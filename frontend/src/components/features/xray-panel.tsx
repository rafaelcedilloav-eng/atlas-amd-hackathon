"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

// ── Types ─────────────────────────────────────────────────────────────────────

interface AuditEvent {
  event_id: string;
  audit_id: string;
  timestamp: string;
  agent: "vision" | "compliance" | "reasoning" | "validator" | "explainer" | "orchestrator";
  stage: "start" | "processing" | "complete" | "error";
  message: string;
  detail?: Record<string, unknown>;
  progress_pct: number;
  severity: "info" | "warning" | "error" | "success";
}

type AgentStatus = "idle" | "active" | "completed" | "error";

interface AgentNode {
  id: string;
  label: string;
  icon: string;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const AGENTS: AgentNode[] = [
  { id: "vision",     label: "Vision",     icon: "👁" },
  { id: "compliance", label: "Compliance", icon: "⚖" },
  { id: "reasoning",  label: "Reasoning",  icon: "🧠" },
  { id: "validator",  label: "Validator",  icon: "🔒" },
  { id: "explainer",  label: "Explainer",  icon: "📄" },
];

const AGENT_COLOR: Record<string, string> = {
  vision:       "#33B5E5",
  compliance:   "#FF8800",
  reasoning:    "#AA66CC",
  validator:    "#FFBB33",
  explainer:    "#00C851",
  orchestrator: "#ED1C24",
};

const SEV_COLOR: Record<string, string> = {
  info:    "#CCCCCC",
  warning: "#FFBB33",
  error:   "#ED1C24",
  success: "#00C851",
};

const SEV_ICON: Record<string, string> = {
  info: "›", warning: "⚠", error: "✗", success: "✓",
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// ── Component ─────────────────────────────────────────────────────────────────

interface XRayPanelProps {
  /** null → idle state, string → connect to that audit stream */
  auditId: string | null;
  /** "uploading" shows a connecting animation before auditId is known */
  phase?: "idle" | "uploading" | "complete";
  onReset?: () => void;
}

export function XRayPanel({ auditId, phase = "idle", onReset }: XRayPanelProps) {
  const [events,      setEvents]      = useState<AuditEvent[]>([]);
  const [statuses,    setStatuses]    = useState<Record<string, AgentStatus>>({});
  const [progress,    setProgress]    = useState(0);
  const [connected,   setConnected]   = useState(false);
  const [complete,    setComplete]    = useState(false);
  const logEndRef   = useRef<HTMLDivElement>(null);
  const esRef       = useRef<EventSource | null>(null);

  const fmt = (iso: string) =>
    new Date(iso).toLocaleTimeString("es-MX", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });

  const connect = useCallback((id: string) => {
    esRef.current?.close();
    const es = new EventSource(`${API}/stream/${id}`);
    esRef.current = es;

    es.onopen = () => setConnected(true);

    es.onmessage = (ev) => {
      try {
        const data: AuditEvent & { type?: string } = JSON.parse(ev.data);
        if (data.type === "timeout") { es.close(); return; }

        setEvents((prev) => {
          // Deduplicate by event_id
          if (prev.some((e) => e.event_id === data.event_id)) return prev;
          return [...prev, data];
        });
        setProgress(data.progress_pct);

        setStatuses((prev) => {
          const next = { ...prev };
          if (data.stage === "start")    next[data.agent] = "active";
          if (data.stage === "complete") next[data.agent] = "completed";
          if (data.stage === "error")    next[data.agent] = "error";
          return next;
        });

        if (data.agent === "orchestrator" && data.stage === "complete") {
          setComplete(true);
          es.close();
        }
      } catch { /* ignore parse errors */ }
    };

    es.onerror = () => {
      setConnected(false);
      es.close();
    };
  }, []);

  useEffect(() => {
    if (auditId) {
      setEvents([]);
      setStatuses({});
      setProgress(0);
      setComplete(false);
      connect(auditId);
    } else {
      esRef.current?.close();
      setEvents([]);
      setStatuses({});
      setProgress(0);
      setComplete(false);
      setConnected(false);
    }
    return () => { esRef.current?.close(); };
  }, [auditId, connect]);

  // Auto-scroll
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const isIdle      = phase === "idle"      && !auditId;
  const isUploading = phase === "uploading" && !auditId;

  return (
    <div className="w-full h-full flex flex-col overflow-hidden">

      {/* Header row */}
      <div className="px-5 py-3 border-b border-white/[0.04] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
            complete    ? "bg-green-500" :
            connected   ? "bg-red-500 animate-pulse" :
            isUploading ? "bg-yellow-500 animate-pulse" :
            "bg-white/20"
          }`} />
          <span className="text-[9px] font-mono font-bold uppercase tracking-[0.3em] text-red-500">
            X&#8209;RAY&nbsp;//&nbsp;Forensic_Reasoning_Theater
          </span>
        </div>
        <div className="flex items-center gap-3">
          {auditId && (
            <span className="text-[8px] font-mono text-white/20">
              {auditId.slice(0, 12)}…
            </span>
          )}
          {complete && (
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="px-2 py-0.5 bg-green-900/20 text-green-400 text-[8px] font-mono border border-green-800/50 uppercase tracking-widest"
            >
              COMPLETE
            </motion.span>
          )}
          {complete && onReset && (
            <button
              onClick={onReset}
              className="text-[8px] font-mono text-white/20 hover:text-white/60 transition-colors"
            >
              ✕ reset
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 flex overflow-hidden">

        {/* Agent graph — left column */}
        <div className="w-[7.5rem] border-r border-white/[0.04] p-3 flex flex-col gap-1 overflow-hidden">
          {AGENTS.map((agent, idx) => {
            const status: AgentStatus = statuses[agent.id] || "idle";
            const color =
              status === "active"    ? "#FFBB33" :
              status === "completed" ? "#00C851" :
              status === "error"     ? "#ED1C24" :
              "#333333";

            return (
              <div key={agent.id} className="flex flex-col items-center">
                <motion.div
                  className="w-11 h-11 rounded-full flex items-center justify-center text-base relative"
                  style={{
                    border: `2px solid ${color}`,
                    background: `${color}10`,
                  }}
                  animate={status === "active" ? {
                    boxShadow: [
                      `0 0 0 0 ${color}40`,
                      `0 0 0 10px ${color}00`,
                      `0 0 0 0 ${color}00`,
                    ],
                  } : {}}
                  transition={status === "active" ? { duration: 1.4, repeat: Infinity } : {}}
                >
                  <span>{agent.icon}</span>
                  {status === "completed" && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center text-[8px] font-bold"
                    >
                      ✓
                    </motion.div>
                  )}
                  {status === "error" && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center text-[8px]"
                    >
                      !
                    </motion.div>
                  )}
                </motion.div>

                <span
                  className="text-[7px] font-mono uppercase tracking-wider mt-1"
                  style={{ color }}
                >
                  {agent.label}
                </span>

                {idx < AGENTS.length - 1 && (
                  <motion.div
                    className="w-px mt-1"
                    style={{
                      height: 10,
                      background: statuses[agent.id] === "completed"
                        ? "linear-gradient(to bottom, #00C851, #333)"
                        : "#333",
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Log stream */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-3 space-y-px font-mono text-[10px]">

            {/* Idle placeholder */}
            {isIdle && (
              <div className="flex flex-col items-center justify-center h-full gap-3 opacity-20 py-8">
                <div className="w-8 h-8 border border-white/20 rounded-full flex items-center justify-center text-lg">⏳</div>
                <span className="text-[9px] uppercase tracking-[0.3em]">Awaiting_Document…</span>
              </div>
            )}

            {/* Uploading placeholder */}
            {isUploading && (
              <div className="flex flex-col items-center justify-center h-full gap-3 py-8">
                <motion.div
                  className="w-8 h-8 border-2 border-red-500/50 rounded-full border-t-red-500"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                />
                <span className="text-[9px] uppercase tracking-[0.3em] text-red-500/70 animate-pulse">
                  Connecting_to_Pipeline…
                </span>
              </div>
            )}

            {/* Events */}
            <AnimatePresence initial={false}>
              {events.map((evt) => (
                <motion.div
                  key={evt.event_id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.12 }}
                  className="flex gap-2 items-baseline py-px hover:bg-white/[0.025] px-1 rounded"
                >
                  <span className="text-white/25 shrink-0 tabular-nums text-[9px]">{fmt(evt.timestamp)}</span>
                  <span
                    className="shrink-0 font-bold uppercase text-[8px] tracking-wider w-16"
                    style={{ color: AGENT_COLOR[evt.agent] || "#CCC" }}
                  >
                    {evt.agent}
                  </span>
                  <span
                    className="shrink-0 text-[9px]"
                    style={{ color: SEV_COLOR[evt.severity] }}
                  >
                    {SEV_ICON[evt.severity]}
                  </span>
                  <span className="text-white/60 break-all leading-snug">{evt.message}</span>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={logEndRef} />
          </div>

          {/* Progress bar */}
          <div className="px-4 py-2 border-t border-white/[0.04] shrink-0">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: progress === 100 ? "#00C851" : "#ED1C24" }}
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>
              <span className="text-[8px] font-mono text-white/20 w-8 text-right tabular-nums">
                {progress}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
