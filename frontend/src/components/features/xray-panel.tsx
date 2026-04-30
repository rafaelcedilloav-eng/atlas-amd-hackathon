"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface AuditEvent {
  event_id: string;
  audit_id: string;
  timestamp: string;
  agent: "vision" | "compliance" | "reasoning" | "validator" | "explainer" | "orchestrator";
  stage: "start" | "processing" | "complete" | "error";
  message: string;
  detail?: Record<string, any>;
  progress_pct: number;
  severity: "info" | "warning" | "error" | "success";
  type?: string; // Para manejar el evento 'timeout'
}

interface AgentNode {
  id: string;
  label: string;
  icon: string;
  status: "idle" | "active" | "completed" | "error";
}

const AGENTS: AgentNode[] = [
  { id: "vision", label: "Vision", icon: "👁", status: "idle" },
  { id: "compliance", label: "Compliance", icon: "⚖", status: "idle" },
  { id: "reasoning", label: "Reasoning", icon: "🧠", status: "idle" },
  { id: "validator", label: "Validator", icon: "🔒", status: "idle" },
  { id: "explainer", label: "Explainer", icon: "📄", status: "idle" },
];

const AGENT_COLORS: Record<string, string> = {
  vision: "#33B5E5",
  compliance: "#FF8800",
  reasoning: "#AA66CC",
  validator: "#FFBB33",
  explainer: "#00C851",
  orchestrator: "#ED1C24",
};

const SEVERITY_COLORS: Record<string, string> = {
  info: "#CCCCCC",
  warning: "#FFBB33",
  error: "#ED1C24",
  success: "#00C851",
};

const MAX_EVENTS = 500;

export default function XRayPanel({ auditId }: { auditId: string }) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [agentStates, setAgentStates] = useState<Record<string, AgentNode["status"]>>({});
  const [progress, setProgress] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const logEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const isCompleteRef = useRef(false);
  const eventIdsRef = useRef<Set<string>>(new Set());

  // Manejo robusto de progreso
  const updateProgress = useCallback((newProgress: number) => {
    setProgress(prev => {
      // Solo actualizar si es un progreso válido y mayor al actual
      if (newProgress >= 0 && newProgress <= 100 && newProgress > prev) {
        return newProgress;
      }
      return prev;
    });
  }, []);

  // Manejo de eventos duplicados
  const addEvent = useCallback((event: AuditEvent) => {
    setEvents(prev => {
      // Evitar eventos duplicados
      if (eventIdsRef.current.has(event.event_id)) {
        return prev;
      }
      
      eventIdsRef.current.add(event.event_id);
      
      // Limitar número de eventos para performance
      const newEvents = [...prev, event];
      if (newEvents.length > MAX_EVENTS) {
        const excess = newEvents.length - MAX_EVENTS;
        newEvents.splice(0, excess);
        // Limpiar IDs antiguos
        for (let i = 0; i < excess; i++) {
          eventIdsRef.current.delete(newEvents[i].event_id);
        }
      }
      
      return newEvents;
    });
  }, []);

  // Actualizar estado de agentes
  const updateAgentStatus = useCallback((agent: string, stage: string) => {
    setAgentStates(prev => {
      const newState = { ...prev };
      
      switch (stage) {
        case "start":
          newState[agent] = "active";
          break;
        case "complete":
          newState[agent] = "completed";
          break;
        case "error":
          newState[agent] = "error";
          break;
        default:
          // Para processing, mantener estado actual si ya está activo
          if (newState[agent] !== "active") {
            newState[agent] = "active";
          }
      }
      
      return newState;
    });
  }, []);

  // Conexión SSE robusta
  const connect = useCallback(() => {
    if (!auditId || isCompleteRef.current) return;
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const es = new EventSource(`${apiUrl}/stream/${auditId}`);
      eventSourceRef.current = es;
      
      es.onopen = () => {
        setIsConnected(true);
        setError(null);
      };
      
      es.onmessage = (event) => {
        try {
          const data: AuditEvent = JSON.parse(event.data);
          
          // Manejo de eventos especiales
          if (data.type === "timeout") {
            setError("Conexión timeout");
            es.close();
            return;
          }
          
          // Validar estructura del evento
          if (!data.event_id || !data.agent || !data.stage) {
            console.warn("Evento inválido recibido:", data);
            return;
          }
          
          addEvent(data);
          
          // Actualizar progreso si es válido
          if (typeof data.progress_pct === 'number' && data.progress_pct >= 0) {
            updateProgress(data.progress_pct);
          }
          
          // Actualizar estado del agente
          updateAgentStatus(data.agent, data.stage);
          
          // Verificar finalización
          if (data.stage === "complete" && data.agent === "orchestrator") {
            isCompleteRef.current = true;
            setIsComplete(true);
            es.close();
          }
        } catch (parseError) {
          console.error("Error parsing SSE event:", parseError);
        }
      };
      
      es.onerror = (err) => {
        setIsConnected(false);
        setError("Error de conexión SSE");
        es.close();
        
        // Reintentar conexión si no está completa
        if (!isCompleteRef.current) {
          setTimeout(connect, 5000);
        }
      };
    } catch (connectionError) {
      console.error("Error estableciendo conexión SSE:", connectionError);
      setError("Error de conexión");
      
      if (!isCompleteRef.current) {
        setTimeout(connect, 5000);
      }
    }
  }, [auditId, addEvent, updateProgress, updateAgentStatus]);

  // Resetear estado cuando cambia el auditId
  useEffect(() => {
    if (!auditId) return;
    
    // Limpiar estado anterior
    setEvents([]);
    setAgentStates({});
    setProgress(0);
    setIsConnected(false);
    setIsComplete(false);
    setError(null);
    eventIdsRef.current.clear();
    isCompleteRef.current = false;
    
    // Cerrar conexión anterior
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    // Establecer nueva conexión
    connect();
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [auditId, connect]);

  // Auto-scroll de logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  // Formateo de tiempo robusto
  const formatTime = useCallback((iso: string) => {
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) throw new Error("Invalid date");
      return d.toLocaleTimeString("es-MX", { 
        hour12: false, 
        hour: "2-digit", 
        minute: "2-digit", 
        second: "2-digit" 
      });
    } catch (e) {
      return "--:--:--";
    }
  }, []);

  return (
    <div className="w-full h-full bg-[#0a0a0a] border border-[#333] rounded-lg overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#333] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            error ? "bg-red-500" : 
            isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"
          }`} />
          <h2 className="text-sm font-mono font-bold text-white tracking-wider">
            X-RAY // FORENSIC REASONING THEATER
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-[#666]">
            {auditId?.slice(0, 16) || "ID_PENDING"}...
          </span>
          {isComplete && (
            <span className="px-2 py-0.5 bg-green-900/30 text-green-400 text-xs font-mono rounded border border-green-800">
              COMPLETE
            </span>
          )}
          {error && (
            <span className="px-2 py-0.5 bg-red-900/30 text-red-400 text-xs font-mono rounded border border-red-800">
              ERROR
            </span>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Agent Graph */}
        <div className="w-48 border-r border-[#333] p-4 flex flex-col gap-4 overflow-y-auto">
          {AGENTS.map((agent, idx) => {
            const status = agentStates[agent.id] || "idle";
            const isActive = status === "active";
            const isCompleted = status === "completed";
            const isError = status === "error";

            return (
              <div key={agent.id} className="flex flex-col items-center gap-2">
                <motion.div
                  className={`w-14 h-14 rounded-full flex items-center justify-center text-xl border-[3px] relative
                    ${isActive ? "border-[#FFBB33]" : 
                      isCompleted ? "border-[#00C851]" : 
                      isError ? "border-[#ED1C24]" : "border-[#333]"}
                    ${isActive ? "bg-[#FFBB33]/10" : 
                      isCompleted ? "bg-[#00C851]/10" : 
                      isError ? "bg-[#ED1C24]/10" : "bg-[#1a1a1a]"}
                  `}
                  animate={isActive ? {
                    boxShadow: [
                      "0 0 0 0 rgba(255,187,51,0.4)", 
                      "0 0 0 12px rgba(255,187,51,0)", 
                      "0 0 0 0 rgba(255,187,51,0)"
                    ],
                  } : {}}
                  transition={isActive ? { duration: 1.5, repeat: Infinity } : {}}
                >
                  <span>{agent.icon}</span>
                  {isCompleted && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-1 -right-1 w-5 h-5 bg-[#00C851] rounded-full flex items-center justify-center text-xs"
                    >
                      ✓
                    </motion.div>
                  )}
                  {isError && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-1 -right-1 w-5 h-5 bg-[#ED1C24] rounded-full flex items-center justify-center text-xs"
                    >
                      !
                    </motion.div>
                  )}
                </motion.div>
                <span className={`text-[10px] font-mono uppercase tracking-wider
                  ${isActive ? "text-[#FFBB33]" : 
                    isCompleted ? "text-[#00C851]" : 
                    isError ? "text-[#ED1C24]" : "text-[#666]"}
                `}>
                  {agent.label}
                </span>
                {idx < AGENTS.length - 1 && (
                  <div className="w-0.5 h-4 bg-[#333]" />
                )}
              </div>
            );
          })}
        </div>

        {/* Live Logs */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-3 font-mono text-[11px] leading-relaxed space-y-1 bg-black/40">
            <AnimatePresence>
              {events.map((event) => (
                <motion.div
                  key={event.event_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.1 }}
                  className="flex gap-2 items-start"
                >
                  <span className="text-[#666] shrink-0">{formatTime(event.timestamp)}</span>
                  <span
                    className="shrink-0 font-bold uppercase w-16"
                    style={{ color: AGENT_COLORS[event.agent] || "#CCC" }}
                  >
                    [{event.agent}]
                  </span>
                  <span
                    className="shrink-0"
                    style={{ color: SEVERITY_COLORS[event.severity] }}
                  >
                    {event.severity === "error" ? "✗" : 
                     event.severity === "success" ? "✓" : "›"}
                  </span>
                  <span className="text-[#CCC] break-all">{event.message}</span>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={logEndRef} />
          </div>

          {/* Progress Bar */}
          <div className="px-3 py-2 border-t border-[#333] bg-[#0a0a0a]">
            <div className="flex items-center gap-3">
              <div className="flex-1 h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ 
                    backgroundColor: progress === 100 ? "#00C851" : "#33B5E5" 
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <span className="text-xs font-mono text-[#666] w-10 text-right">
                {Math.round(progress)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
