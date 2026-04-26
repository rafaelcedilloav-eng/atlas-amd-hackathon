import {
  PipelineResult,
  AtlasAuditRow,
  HumanDecision,
  StatsResponse,
  AuditListItem,
} from "@/types/atlas";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export const atlasApi = {
  analyze: async (pdfPath: string): Promise<PipelineResult> => {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pdf_path: pdfPath }),
    });
    if (!res.ok) throw new Error("Error al analizar el documento");
    return res.json();
  },

  uploadFile: async (file: File): Promise<PipelineResult> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Error desconocido" }));
      throw new Error(err.detail || "Error al subir el archivo");
    }
    return res.json();
  },

  getResult: async (documentId: string): Promise<AtlasAuditRow> => {
    const res = await fetch(`${API_BASE_URL}/result/${documentId}`);
    if (!res.ok) throw new Error("Resultado no encontrado");
    return res.json();
  },

  getAudits: async (limit = 20): Promise<{ audits: AuditListItem[]; total: number }> => {
    const res = await fetch(`${API_BASE_URL}/audits?limit=${limit}`);
    if (!res.ok) throw new Error("Error al obtener auditorías");
    return res.json();
  },

  getStats: async (): Promise<StatsResponse> => {
    const res = await fetch(`${API_BASE_URL}/stats`);
    if (!res.ok) throw new Error("Error al obtener estadísticas");
    return res.json();
  },

  submitDecision: async (documentId: string, decision: HumanDecision): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/human_decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId, decision }),
    });
    if (!res.ok) throw new Error("Error al registrar decisión");
  },
};
