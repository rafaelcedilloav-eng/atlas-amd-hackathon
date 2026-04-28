"use client";

import { useState, useRef, DragEvent } from "react";
import { useRouter } from "next/navigation";
import { Upload, X, FileText, Loader2, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { atlasApi } from "@/services/api";
import { cn } from "@/lib/utils";

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
}

type UploadStatus = "idle" | "uploading" | "processing" | "error";

export function UploadModal({ open, onClose }: UploadModalProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const handleFile = (f: File) => {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Solo se aceptan archivos PDF.");
      return;
    }
    if (f.size > 20 * 1024 * 1024) {
      setError("Archivo demasiado grande (máximo 20 MB).");
      return;
    }
    setError(null);
    setFile(f);
    setStatus("idle");
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFile(dropped);
  };

  const handleSubmit = async () => {
    if (!file || status === "uploading" || status === "processing") return;

    setStatus("uploading");
    setError(null);

    try {
      // Fase 1: Upload (rápida)
      const result = await atlasApi.uploadFile(file);

      // Fase 2: Processing (lenta, ~52s)
      setStatus("processing");

      // En este pipeline, uploadFile ya retorna el resultado final porque el backend
      // espera a que termine el procesamiento antes de responder.
      // Si el backend fuera asíncrono, aquí haríamos polling.

      onClose();
      router.push(`/audits/${result.document_id}`);
    } catch (err) {
      const errorMessage = (err as Error).message;
      setStatus("error");
      if (errorMessage.includes("401")) {
        setError("API Key inválida — verifica la configuración.");
      } else if (errorMessage.includes("413")) {
        setError("Archivo demasiado grande (máximo 20 MB).");
      } else {
        setError(errorMessage || "Error al procesar el documento.");
      }
    }
  };

  const reset = () => {
    setFile(null);
    setStatus("idle");
    setError(null);
  };

  const handleClose = () => {
    if (status === "uploading" || status === "processing") return;
    reset();
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-md"
            onClick={handleClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-8 w-full max-w-md space-y-6 shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden"
          >
            {/* AMD Accent Line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-amd-red to-transparent opacity-70" />

            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-black tracking-tighter uppercase text-white">
                  Nueva <span className="text-amd-red">Auditoría</span>
                </h3>
                <p className="text-xs font-mono text-amd-gray-500 uppercase tracking-widest mt-1">
                  DeepSeek-R1 / AMD MI300X Pipeline
                </p>
              </div>
              <button
                onClick={handleClose}
                disabled={status === "uploading" || status === "processing"}
                className="w-8 h-8 bg-white/5 rounded flex items-center justify-center hover:bg-amd-red hover:text-white transition-all disabled:opacity-20"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drop Zone */}
            {!file ? (
              <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={cn(
                  "border border-dashed rounded-lg p-10 flex flex-col items-center gap-4 cursor-pointer transition-all duration-300",
                  dragging
                    ? "border-amd-red bg-amd-red/5"
                    : "border-amd-gray-700 hover:border-amd-red/50 hover:bg-white/5"
                )}
              >
                <div className={cn(
                  "w-14 h-14 rounded flex items-center justify-center transition-all duration-300",
                  dragging ? "bg-amd-red/20 shadow-[0_0_20px_rgba(237,28,36,0.2)]" : "bg-amd-gray-800"
                )}>
                  <Upload className={cn("w-7 h-7", dragging ? "text-amd-red" : "text-amd-gray-500")} />
                </div>
                <div className="text-center">
                  <p className="text-sm text-amd-gray-300 font-medium">
                    Arrastra tu PDF aquí o{" "}
                    <span className="text-amd-red hover:underline">selecciona un archivo</span>
                  </p>
                  <p className="text-[10px] font-mono text-amd-gray-500 mt-2 uppercase tracking-tight">
                    Máximo 20MB · Formato PDF Estándar
                  </p>
                </div>
                <input
                  ref={inputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                />
              </div>
            ) : (
              <div className="bg-amd-gray-950 border border-amd-gray-800 rounded-lg p-5 flex items-center gap-4 relative group">
                <div className="w-12 h-12 bg-amd-red/10 border border-amd-red/20 rounded flex items-center justify-center shrink-0">
                  <FileText className="w-6 h-6 text-amd-red" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-white truncate text-sm uppercase tracking-tight">{file.name}</p>
                  <p className="text-[10px] font-mono text-amd-gray-500 tracking-tighter">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB / READY_FOR_INFERENCE
                  </p>
                </div>
                {(status === "idle" || status === "error") && (
                  <button
                    onClick={reset}
                    className="text-amd-gray-500 hover:text-amd-red transition-colors shrink-0"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
                {/* Progress bar pulse for processing */}
                {(status === "uploading" || status === "processing") && (
                  <div className="absolute bottom-0 left-0 h-[1px] bg-amd-red animate-[shimmer_2s_infinite] w-full" />
                )}
              </div>
            )}

            {/* Status messages */}
            {(status === "uploading" || status === "processing") && (
              <div className="bg-amd-gray-950 border border-amd-gray-800 rounded-lg p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-4 h-4 text-amd-red animate-spin" />
                    <span className="text-xs font-mono font-bold text-white uppercase tracking-widest">
                      {status === "uploading" ? "Subiendo_Binarios" : "Ejecutando_Inferencia"}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-amd-red">
                    {status === "uploading" ? "LOCAL -> CLOUD" : "AMD_MI300X_ACTIVE"}
                  </span>
                </div>

                {/* Technical Progress Bar */}
                <div className="h-1 bg-amd-gray-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: "0%" }}
                    animate={{ width: status === "uploading" ? "30%" : "90%" }}
                    transition={{ duration: status === "uploading" ? 2 : 45, ease: "linear" }}
                    className="h-full bg-amd-red shadow-[0_0_10px_rgba(237,28,36,0.5)]"
                  />
                </div>

                <p className="text-[10px] font-mono text-amd-gray-500 leading-relaxed uppercase">
                  {status === "uploading" 
                    ? "> Estableciendo canal seguro... transfiriendo bloques de datos."
                    : "> DeepSeek-R1 analizando consistencia forense. Tiempo estimado: 52s."}
                </p>
              </div>
            )}

            {error && (
              <div className="bg-amd-red/5 border border-amd-red/20 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amd-red shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-mono font-bold text-amd-red uppercase tracking-tight">Critical_Error</p>
                  <p className="text-xs text-amd-gray-300 mt-1 leading-normal">{error}</p>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleClose}
                disabled={status === "uploading" || status === "processing"}
                className="flex-1 py-4 bg-amd-gray-800 hover:bg-amd-gray-700 text-white text-xs font-bold uppercase tracking-widest rounded transition-all disabled:opacity-20"
              >
                Abordar
              </button>
              <button
                onClick={handleSubmit}
                disabled={!file || status === "uploading" || status === "processing"}
                className="flex-1 py-4 bg-amd-red hover:bg-amd-red-deep disabled:opacity-20 disabled:cursor-not-allowed text-white text-xs font-black uppercase tracking-widest rounded transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(237,28,36,0.15)] hover:shadow-[0_0_30px_rgba(237,28,36,0.3)]"
              >
                {status === "uploading" || status === "processing" ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                {status === "uploading" ? "Transmitiendo..." : status === "processing" ? "Procesando" : "Iniciar Análisis"}
              </button>
            </div>

            {/* Rafael's Spark - Subtle technical quote */}
            <div className="text-center pt-2">
              <p className="text-[9px] font-mono text-amd-gray-700 italic">
                "La precisión no es un acto, es el hábito de la arquitectura técnica."
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
