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

type UploadStatus = "idle" | "uploading" | "error";

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
    if (!file || status === "uploading") return;
    setStatus("uploading");
    setError(null);
    try {
      const result = await atlasApi.uploadFile(file);
      onClose();
      router.push(`/audits/${result.document_id}`);
    } catch (err) {
      setStatus("error");
      setError((err as Error).message || "Error al procesar el documento.");
    }
  };

  const reset = () => {
    setFile(null);
    setStatus("idle");
    setError(null);
  };

  const handleClose = () => {
    if (status === "uploading") return;
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
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={handleClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative bg-slate-900 border border-white/10 rounded-3xl p-8 w-full max-w-md space-y-6 shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-black tracking-tighter">Nueva Auditoría</h3>
                <p className="text-sm text-white/40">
                  Sube un PDF para iniciar el análisis forense con DeepSeek-R1.
                </p>
              </div>
              <button
                onClick={handleClose}
                disabled={status === "uploading"}
                className="w-8 h-8 bg-white/5 rounded-lg flex items-center justify-center hover:bg-white/10 transition-all disabled:opacity-40"
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
                  "border-2 border-dashed rounded-2xl p-10 flex flex-col items-center gap-3 cursor-pointer transition-all",
                  dragging
                    ? "border-blue-500 bg-blue-500/10"
                    : "border-white/10 hover:border-white/30 hover:bg-white/5"
                )}
              >
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center transition-all",
                  dragging ? "bg-blue-500/20" : "bg-white/5"
                )}>
                  <Upload className={cn("w-6 h-6", dragging ? "text-blue-400" : "text-white/30")} />
                </div>
                <div className="text-center">
                  <p className="text-sm text-white/60">
                    Arrastra tu PDF aquí o{" "}
                    <span className="text-blue-400 font-semibold">selecciona un archivo</span>
                  </p>
                  <p className="text-xs text-white/30 mt-1">Solo archivos .pdf</p>
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
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4 flex items-center gap-4">
                <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5 text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white truncate">{file.name}</p>
                  <p className="text-xs text-white/40">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                {status !== "uploading" && (
                  <button
                    onClick={reset}
                    className="text-white/30 hover:text-white transition-colors shrink-0"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}

            {/* Status messages */}
            {status === "uploading" && (
              <div className="bg-blue-600/10 border border-blue-600/20 rounded-xl px-4 py-3 flex items-center gap-3">
                <Loader2 className="w-4 h-4 text-blue-400 animate-spin shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-blue-400">Analizando documento...</p>
                  <p className="text-xs text-white/40">
                    DeepSeek-R1 procesando. Puede tomar 30–90 segundos.
                  </p>
                </div>
              </div>
            )}

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 flex items-center gap-3">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleClose}
                disabled={status === "uploading"}
                className="flex-1 py-3 bg-white/5 border border-white/10 hover:bg-white/10 text-white/60 font-bold rounded-xl transition-all disabled:opacity-40"
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmit}
                disabled={!file || status === "uploading"}
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20"
              >
                {status === "uploading" ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                {status === "uploading" ? "Procesando..." : "Iniciar Auditoría"}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
