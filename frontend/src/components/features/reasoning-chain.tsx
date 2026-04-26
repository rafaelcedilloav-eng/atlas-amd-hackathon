"use client";

import { ReasoningStep } from "@/types/atlas";
import { motion } from "framer-motion";
import { CheckCircle2, ChevronRight, Info } from "lucide-react";

interface ReasoningChainProps {
  steps: ReasoningStep[];
}

export const ReasoningChain = ({ steps }: ReasoningChainProps) => {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <motion.div
          key={step.step}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.2 }}
          className="relative pl-8 pb-4 border-l border-white/10 last:border-0"
        >
          <div className="absolute left-[-9px] top-0 w-4 h-4 rounded-full bg-blue-500 border-4 border-slate-950 flex items-center justify-center">
             <div className="w-1.5 h-1.5 rounded-full bg-white" />
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4 hover:border-white/20 transition-colors">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono text-blue-400 uppercase tracking-tighter">
                Paso {step.step}
              </span>
              <ChevronRight className="w-3 h-3 text-white/30" />
              <h4 className="font-semibold text-white/90">{step.description}</h4>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
              <div className="space-y-1">
                <span className="text-[10px] text-white/40 uppercase font-bold flex items-center gap-1">
                  <Info className="w-3 h-3" /> Evidencia
                </span>
                <p className="text-sm text-white/70 italic">"{step.evidence}"</p>
              </div>
              <div className="space-y-1">
                <span className="text-[10px] text-emerald-400 uppercase font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Conclusión
                </span>
                <p className="text-sm text-emerald-400/90 font-medium">{step.conclusion}</p>
              </div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
};
