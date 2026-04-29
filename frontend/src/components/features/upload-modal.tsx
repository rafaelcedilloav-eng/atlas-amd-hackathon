"use client";

import { useState, useRef, DragEvent, useCallback } from "react";
import {
  Upload, X, FileText, Loader2, AlertCircle,
  CheckCircle2, Clock, ChevronRight,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { atlasApi } from "@/services/api";
import { cn } from "@/lib/utils";

const MAX_FILES = 10;
const MAX_SIZE_MB = 20;

type FileStatus = "waiting" | "processing" | "done" | "error";

interface QueueItem {
  id: string;
  file: File;
  status: FileStatus;
  error?: string;
}

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
}

export function UploadModal({ open, onClose }: UploadModalProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [dragging, setDragging] = useState(false);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const doneCount = queue.filter((i) => i.status === "done").length;
  const allDone = queue.length > 0 && queue.every((i) => i.status === "done" || i.status === "error");

  const addFiles = useCallback((incoming: FileList | File[]) => {
    const files = Array.from(incoming);
    const errors: string[] = [];
    const valid: QueueItem[] = [];

    for (const f of files) {
      if (!f.name.toLowerCase().endsWith(".pdf")) {
        errors.push(`${f.name}: only PDF files accepted.`);
        continue;
      }
      if (f.size > MAX_SIZE_MB * 1024 * 1024) {
        errors.push(`${f.name}: exceeds ${MAX_SIZE_MB} MB limit.`);
        continue;
      }
      valid.push({
        id: `${f.name}-${f.size}-${Date.now()}-${Math.random()}`,
        file: f,
        status: "waiting",
      });
    }

    setGlobalError(errors.length ? errors.join(" ") : null);

    setQueue((prev) => {
      const combined = [...prev, ...valid];
      if (combined.length > MAX_FILES) {
        setGlobalError((e) => `${e ? e + " " : ""}Queue limited to ${MAX_FILES} files.`);
        return combined.slice(0, MAX_FILES);
      }
      return combined;
    });
  }, []);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const removeItem = (id: string) => {
    setQueue((prev) => prev.filter((i) => i.id !== id));
  };

  const handleSubmit = async () => {
    if (isRunning || queue.length === 0) return;
    setIsRunning(true);
    setGlobalError(null);

    const waiting = queue.filter((i) => i.status === "waiting");

    for (const item of waiting) {
      setQueue((prev) =>
        prev.map((qi) => (qi.id === item.id ? { ...qi, status: "processing" as FileStatus } : qi))
      );
      try {
        await atlasApi.uploadFile(item.file);
        setQueue((prev) =>
          prev.map((qi) => (qi.id === item.id ? { ...qi, status: "done" as FileStatus } : qi))
        );
      } catch (err) {
        const msg = (err as Error).message || "Processing failed.";
        setQueue((prev) =>
          prev.map((qi) =>
            qi.id === item.id ? { ...qi, status: "error" as FileStatus, error: msg.slice(0, 70) } : qi
          )
        );
      }
    }

    setIsRunning(false);
    queryClient.invalidateQueries({ queryKey: ["audits"] });
    queryClient.invalidateQueries({ queryKey: ["recent-audits"] });
    queryClient.invalidateQueries({ queryKey: ["atlas-stats"] });
  };

  const handleClose = () => {
    if (isRunning) return;
    setQueue([]);
    setGlobalError(null);
    onClose();
  };

  const clearQueue = () => {
    if (isRunning) return;
    setQueue([]);
    setGlobalError(null);
  };

  const slotsLeft = MAX_FILES - queue.length;

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-md"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-8 w-full max-w-lg space-y-6 shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden"
          >
            {/* AMD Accent Line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-amd-red to-transparent opacity-70" />

            {/* Hidden file input — always mounted */}
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              multiple
              className="hidden"
              onChange={(e) => e.target.files && addFiles(e.target.files)}
            />

            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-black tracking-tighter uppercase text-white">
                  {allDone ? "Batch" : "New"} <span className="text-amd-red">Audit</span>
                </h3>
                <p className="text-xs font-mono text-amd-gray-500 uppercase tracking-widest mt-1">
                  {queue.length === 0
                    ? "DeepSeek-R1 / AMD MI300X Pipeline"
                    : `${queue.length} file${queue.length !== 1 ? "s" : ""} queued · max ${MAX_FILES} · ${MAX_SIZE_MB} MB each`}
                </p>
              </div>
              <button
                onClick={handleClose}
                disabled={isRunning}
                className="w-8 h-8 bg-white/5 rounded flex items-center justify-center hover:bg-amd-red hover:text-white transition-all disabled:opacity-20"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drop Zone (empty state) */}
            {queue.length === 0 && (
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
                    Drop PDF files here or{" "}
                    <span className="text-amd-red hover:underline">browse</span>
                  </p>
                  <p className="text-[10px] font-mono text-amd-gray-500 mt-2 uppercase tracking-tight">
                    Up to {MAX_FILES} files · {MAX_SIZE_MB} MB each · PDF only
                  </p>
                </div>
              </div>
            )}

            {/* Queue list */}
            {queue.length > 0 && (
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {queue.map((item, i) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className={cn(
                      "bg-amd-gray-950 border rounded-lg p-4 flex items-center gap-3 relative overflow-hidden",
                      item.status === "processing" && "border-amd-red/40",
                      item.status === "done" && "border-accent-success/30",
                      item.status === "error" && "border-red-500/30",
                      item.status === "waiting" && "border-amd-gray-800",
                    )}
                  >
                    <QueueIcon status={item.status} />
                    <div className="flex-1 min-w-0">
                      <p className="font-mono text-xs font-bold text-white truncate uppercase">
                        {item.file.name}
                      </p>
                      <p className="text-[10px] font-mono text-amd-gray-500 mt-0.5">
                        {(item.file.size / (1024 * 1024)).toFixed(2)} MB
                        {item.error && (
                          <span className="text-red-400 ml-2">{item.error}</span>
                        )}
                      </p>
                    </div>
                    {item.status === "waiting" && !isRunning && (
                      <button
                        onClick={() => removeItem(item.id)}
                        className="text-amd-gray-600 hover:text-amd-red transition-colors shrink-0"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                    {item.status === "processing" && (
                      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-amd-red shadow-[0_0_8px_rgba(237,28,36,0.7)] animate-[shimmer_2s_infinite]" />
                    )}
                  </motion.div>
                ))}
              </div>
            )}

            {/* Add more files link */}
            {queue.length > 0 && slotsLeft > 0 && !isRunning && !allDone && (
              <button
                onClick={() => inputRef.current?.click()}
                className="w-full text-center text-[10px] font-mono text-amd-gray-600 hover:text-amd-red transition-colors uppercase tracking-widest py-1"
              >
                + Add more files ({slotsLeft} slot{slotsLeft !== 1 ? "s" : ""} remaining)
              </button>
            )}

            {/* Error banner */}
            {globalError && (
              <div className="bg-amd-red/5 border border-amd-red/20 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-4 h-4 text-amd-red shrink-0 mt-0.5" />
                <p className="text-xs font-mono text-amd-gray-300 leading-relaxed">{globalError}</p>
              </div>
            )}

            {/* Processing status bar */}
            {isRunning && (
              <div className="bg-amd-gray-950 border border-amd-gray-800 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Loader2 className="w-4 h-4 text-amd-red animate-spin" />
                  <span className="text-xs font-mono font-bold text-white uppercase tracking-widest">
                    Processing_Queue
                  </span>
                </div>
                <span className="text-[10px] font-mono text-amd-red uppercase">
                  {doneCount} / {queue.length} done · AMD_MI300X
                </span>
              </div>
            )}

            {/* Completion banner */}
            {allDone && !isRunning && (
              <div className="bg-accent-success/5 border border-accent-success/20 rounded-lg p-4 flex items-center gap-3">
                <CheckCircle2 className="w-4 h-4 text-accent-success shrink-0" />
                <p className="text-xs font-mono font-bold text-accent-success uppercase tracking-widest">
                  Batch Complete — {doneCount}/{queue.length} Processed Successfully
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              {allDone ? (
                <button
                  onClick={handleClose}
                  className="flex-1 py-4 bg-amd-red hover:bg-amd-red-deep text-white text-xs font-black uppercase tracking-widest rounded transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(237,28,36,0.2)] hover:shadow-[0_0_30px_rgba(237,28,36,0.4)]"
                >
                  <ChevronRight className="w-4 h-4" />
                  View Results
                </button>
              ) : (
                <>
                  <button
                    onClick={handleClose}
                    disabled={isRunning}
                    className="flex-1 py-4 bg-amd-gray-800 hover:bg-amd-gray-700 text-white text-xs font-bold uppercase tracking-widest rounded transition-all disabled:opacity-20"
                  >
                    Abort
                  </button>
                  {queue.length > 0 && !isRunning && (
                    <button
                      onClick={clearQueue}
                      className="py-4 px-5 bg-amd-gray-800 hover:bg-amd-gray-700 text-white text-xs font-bold uppercase tracking-widest rounded transition-all"
                      title="Clear queue"
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={handleSubmit}
                    disabled={queue.length === 0 || isRunning}
                    className="flex-1 py-4 bg-amd-red hover:bg-amd-red-deep disabled:opacity-20 disabled:cursor-not-allowed text-white text-xs font-black uppercase tracking-widest rounded transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(237,28,36,0.15)] hover:shadow-[0_0_30px_rgba(237,28,36,0.3)]"
                  >
                    {isRunning ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> Processing...</>
                    ) : (
                      <><Upload className="w-4 h-4" /> Start Analysis</>
                    )}
                  </button>
                </>
              )}
            </div>

            <div className="text-center pt-1">
              <p className="text-[9px] font-mono text-amd-gray-700 italic">
                &ldquo;Precision is not an act, it&apos;s the habit of technical architecture.&rdquo;
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

function QueueIcon({ status }: { status: FileStatus }) {
  if (status === "waiting")    return <Clock className="w-4 h-4 text-amd-gray-500 shrink-0" />;
  if (status === "processing") return <Loader2 className="w-4 h-4 text-amd-red animate-spin shrink-0" />;
  if (status === "done")       return <CheckCircle2 className="w-4 h-4 text-accent-success shrink-0" />;
  return <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />;
}
