import { create } from "zustand";

type AuditPhase = "idle" | "uploading" | "complete";

interface AuditState {
  activeAuditId: string | null;
  phase: AuditPhase;
  /** Call when upload starts (no id yet) */
  startUploading: () => void;
  /** Call when pipeline result returns with the real document_id */
  setComplete: (id: string) => void;
  /** Reset panel back to idle */
  reset: () => void;
}

export const useAuditStore = create<AuditState>((set) => ({
  activeAuditId: null,
  phase: "idle",
  startUploading: () => set({ phase: "uploading", activeAuditId: null }),
  setComplete:    (id) => set({ phase: "complete", activeAuditId: id }),
  reset:          () => set({ phase: "idle", activeAuditId: null }),
}));
