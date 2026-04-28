"use client";

import { useQuery } from "@tanstack/react-query";
import { atlasApi } from "@/services/api";
import { ShieldCheck, ShieldAlert, Copy, Ban, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function IntegrityPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["audits-integrity"],
    queryFn: () => atlasApi.getAudits(100),
    refetchInterval: 30000,
  });

  const audits = data?.audits ?? [];
  const duplicates = audits.filter((a) => a.is_duplicate);
  const blacklisted = audits.filter((a) => a.is_blacklisted);
  const clean = audits.filter((a) => !a.is_duplicate && !a.is_blacklisted);

  const StatCard = ({
    icon,
    label,
    value,
    color,
  }: {
    icon: React.ReactNode;
    label: string;
    value: number;
    color: string;
  }) => (
    <div className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-8 space-y-4">
      <div className={`w-12 h-12 rounded flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-3xl font-black text-white">{value}</p>
        <p className="text-xs font-mono text-amd-gray-500 uppercase tracking-widest mt-1">{label}</p>
      </div>
    </div>
  );

  return (
    <div className="p-10 space-y-10">
      <div className="flex items-center gap-4">
        <ShieldCheck className="w-6 h-6 text-amd-red" />
        <div>
          <h2 className="text-2xl font-black tracking-tighter uppercase text-white">
            Integrity <span className="text-amd-red">Gate</span>
          </h2>
          <p className="text-xs font-mono text-amd-gray-500 uppercase tracking-widest mt-1">
            Deduplication_Engine + Blacklist_Validator
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-3 text-amd-gray-500 p-10">
          <Loader2 className="w-5 h-5 animate-spin text-amd-red" />
          <span className="font-mono text-sm uppercase tracking-widest">Analyzing_Integrity</span>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0 }}>
              <StatCard
                icon={<ShieldCheck className="w-6 h-6 text-accent-success" />}
                label="Clean_Documents"
                value={clean.length}
                color="bg-accent-success/10"
              />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
              <StatCard
                icon={<Copy className="w-6 h-6 text-amber-400" />}
                label="Duplicates_Detected"
                value={duplicates.length}
                color="bg-amber-400/10"
              />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <StatCard
                icon={<Ban className="w-6 h-6 text-amd-red" />}
                label="Blocked_Vendors"
                value={blacklisted.length}
                color="bg-amd-red/10"
              />
            </motion.div>
          </div>

          {(duplicates.length > 0 || blacklisted.length > 0) && (
            <div className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg overflow-hidden">
              <div className="px-6 py-4 bg-amd-gray-950 border-b border-amd-gray-800">
                <p className="text-xs font-mono font-bold text-amd-red uppercase tracking-widest">
                  Integrity_Alerts
                </p>
              </div>
              <div className="divide-y divide-amd-gray-800">
                {[...duplicates, ...blacklisted].map((audit) => (
                  <div key={audit.doc_id} className="px-6 py-4 flex items-center justify-between">
                    <span className="font-mono text-xs text-white">{audit.doc_id.slice(0, 32)}…</span>
                    <div className="flex gap-2">
                      {audit.is_duplicate && (
                        <span className="text-[10px] font-mono font-bold bg-amber-400/10 text-amber-400 px-2 py-1 rounded uppercase">
                          Duplicate
                        </span>
                      )}
                      {audit.is_blacklisted && (
                        <span className="text-[10px] font-mono font-bold bg-amd-red/10 text-amd-red px-2 py-1 rounded uppercase">
                          Blacklisted
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {duplicates.length === 0 && blacklisted.length === 0 && audits.length > 0 && (
            <div className="bg-accent-success/5 border border-accent-success/20 rounded-lg p-10 text-center space-y-3">
              <ShieldCheck className="w-12 h-12 text-accent-success mx-auto" />
              <p className="font-mono text-accent-success text-sm uppercase tracking-widest font-bold">
                Integrity_Gate: All Clear
              </p>
              <p className="font-mono text-amd-gray-500 text-xs">
                No duplicate documents or blacklisted vendors detected.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
