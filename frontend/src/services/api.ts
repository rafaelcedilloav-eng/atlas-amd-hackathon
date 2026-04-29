import {
  PipelineResult,
  AtlasAuditRow,
  HumanDecision,
  StatsResponse,
  AuditListItem,
} from "@/types/atlas";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

const authHeaders = (): HeadersInit => ({
  "Content-Type": "application/json",
  "X-API-Key": API_KEY,
});

const uploadHeaders = (): HeadersInit => ({
  "X-API-Key": API_KEY,
});

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

export const atlasApi = {
  analyze: async (pdfPath: string): Promise<PipelineResult> => {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ pdf_path: pdfPath }),
    });
    return handleResponse<PipelineResult>(res);
  },

  uploadFile: async (file: File): Promise<PipelineResult> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      headers: uploadHeaders(),
      body: formData,
    });
    return handleResponse<PipelineResult>(res);
  },

  getResult: async (documentId: string): Promise<AtlasAuditRow> => {
    const res = await fetch(`${API_BASE_URL}/result/${documentId}`, {
      headers: authHeaders(),
    });
    return handleResponse<AtlasAuditRow>(res);
  },

  getAudits: async (
    limit = 20,
    search?: string,
    severity?: string,
  ): Promise<{ audits: AuditListItem[]; total: number }> => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (search?.trim()) params.set("search", search.trim());
    if (severity) params.set("severity", severity);
    const res = await fetch(`${API_BASE_URL}/audit-list?${params}`, {
      headers: authHeaders(),
    });
    return handleResponse<{ audits: AuditListItem[]; total: number }>(res);
  },

  getStats: async (): Promise<StatsResponse> => {
    // /stats es público — no requiere API key
    const res = await fetch(`${API_BASE_URL}/stats`);
    return handleResponse<StatsResponse>(res);
  },

  submitDecision: async (documentId: string, decision: HumanDecision): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/human_decision`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ document_id: documentId, decision }),
    });
    return handleResponse<void>(res);
  },
};
