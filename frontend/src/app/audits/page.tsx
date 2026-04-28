"use client";

import { useQuery } from "@tanstack/react-query";
import { atlasApi } from "@/services/api";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { FileSearch, Loader2, ShieldAlert, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export default function AuditsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["audits"],
    queryFn: () => atlasApi.getAudits(50),
    refetchInterval: 30000,
  });

  return (
    <div className="p-10 space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <FileSearch className="w-6 h-6 text-amd-red" />
          <div>
            <h2 className="text-2xl font-black tracking-tighter uppercase text-white">
              Audit <span className="text-amd-red">Registry</span>
            </h2>
            <p className="text-xs font-mono text-amd-gray-500 uppercase tracking-widest mt-1">
              Forensic_Pipeline_Log — {data?.total ?? 0} documents processed
            </p>
          </div>
        </div>
      </div>

      <div className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg overflow-hidden shadow-2xl">
        {isLoading ? (
          <div className="flex items-center justify-center p-20 gap-3 text-amd-gray-500">
            <Loader2 className="w-5 h-5 animate-spin text-amd-red" />
            <span className="font-mono text-sm uppercase tracking-widest">Loading_Records</span>
          </div>
        ) : error ? (
          <div className="p-10 text-center font-mono text-amd-red text-sm uppercase tracking-widest">
            Error loading audits.
          </div>
        ) : !data?.audits.length ? (
          <div className="p-20 text-center space-y-3">
            <FileSearch className="w-12 h-12 text-amd-gray-700 mx-auto" />
            <p className="font-mono text-amd-gray-500 text-sm uppercase tracking-widest">
              No audits registered yet.
            </p>
            <p className="font-mono text-amd-gray-600 text-xs">
              Upload a document from the Dashboard to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-amd-gray-800">
            <div className="grid grid-cols-12 px-6 py-3 text-[10px] font-mono font-bold text-amd-gray-500 uppercase tracking-widest bg-amd-gray-950">
              <div className="col-span-4">Document ID</div>
              <div className="col-span-2">Severity</div>
              <div className="col-span-2">Confidence</div>
              <div className="col-span-2">Integrity</div>
              <div className="col-span-2">Date</div>
            </div>
            {data.audits.map((audit, i) => (
              <motion.div
                key={audit.doc_id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.02 }}
              >
                <Link
                  href={`/audits/${audit.doc_id}`}
                  className="grid grid-cols-12 px-6 py-4 hover:bg-amd-gray-800 transition-colors group items-center"
                >
                  <div className="col-span-4 font-mono text-xs text-white group-hover:text-amd-red transition-colors truncate pr-4">
                    {audit.doc_id.slice(0, 24)}…
                  </div>
                  <div className="col-span-2">
                    <SeverityBadge severity={(audit.severity as any) ?? "LOW"} />
                  </div>
                  <div className="col-span-2 font-mono text-xs text-amd-gray-400">
                    {audit.confidence_score != null
                      ? `${Math.round(audit.confidence_score * 100)}%`
                      : "—"}
                  </div>
                  <div className="col-span-2 flex items-center gap-1.5">
                    {audit.is_duplicate || audit.is_blacklisted ? (
                      <>
                        <ShieldAlert className="w-3.5 h-3.5 text-amd-red" />
                        <span className="text-[10px] font-mono font-bold text-amd-red uppercase">
                          {audit.is_duplicate ? "DUP" : "BL"}
                        </span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-3.5 h-3.5 text-accent-success" />
                        <span className="text-[10px] font-mono font-bold text-accent-success uppercase">OK</span>
                      </>
                    )}
                  </div>
                  <div className="col-span-2 font-mono text-[10px] text-amd-gray-500">
                    {audit.created_at ? formatDate(audit.created_at) : "—"}
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
