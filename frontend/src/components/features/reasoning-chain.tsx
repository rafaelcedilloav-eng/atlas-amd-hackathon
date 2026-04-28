"use client";

import { ReasoningStep } from "@/types/atlas";
import { motion } from "framer-motion";
import { CheckCircle2, ChevronRight, Terminal, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReasoningChainProps {
  steps: ReasoningStep[];
}

export const ReasoningChain = ({ steps }: ReasoningChainProps) => {
  return (
    <div className="space-y-6 relative before:absolute before:inset-0 before:bg-[radial-gradient(#ED1C2410_1px,transparent_1px)] before:[background-size:20px_20px] before:opacity-20">
      {steps.map((step, index) => (
        <motion.div
          key={step.step}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
          className="relative pl-10 group"
        >
          {/* Vertical Technical Line */}
          {index !== steps.length - 1 && (
            <div className="absolute left-[15px] top-8 bottom-[-24px] w-[1px] bg-gradient-to-b from-amd-red/50 to-transparent" />
          )}

          {/* Node Icon */}
          <div className={cn(
            "absolute left-0 top-0 w-8 h-8 rounded-sm bg-amd-gray-950 border border-amd-gray-800 flex items-center justify-center z-10 group-hover:border-amd-red transition-colors shadow-lg",
            "after:content-[''] after:absolute after:inset-0 after:bg-amd-red/5 group-hover:after:bg-amd-red/20 transition-all"
          )}>
             <span className="text-[10px] font-mono font-black text-amd-red leading-none">{step.step}</span>
          </div>
          
          <div className="bg-amd-gray-900/80 backdrop-blur-sm border border-amd-gray-800 rounded p-6 group-hover:border-amd-gray-700 transition-all shadow-xl relative overflow-hidden">
            {/* Top Accent Line */}
            <div className="absolute top-0 left-0 w-12 h-[1px] bg-amd-red" />
            
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                <Terminal className="w-3 h-3 text-amd-gray-500" />
                <h4 className="font-mono text-xs font-black text-white uppercase tracking-widest">{step.description}</h4>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="w-3 h-3 text-amd-red/60 animate-pulse" />
                <span className="text-[9px] font-mono text-amd-gray-500 uppercase tracking-tighter">THREAD_ACTIVE // {step.step.toString().padStart(2, '0')}</span>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4 border-t border-amd-gray-800 pt-4">
              <div className="space-y-2">
                <span className="text-[9px] text-amd-gray-500 uppercase font-black tracking-widest flex items-center gap-2">
                  <ChevronRight className="w-3 h-3 text-amd-red" /> Captured_Evidence
                </span>
                <p className="text-xs text-amd-gray-300 italic font-medium leading-relaxed bg-amd-black/50 p-3 rounded border border-amd-gray-800/50">
                  "{step.evidence}"
                </p>
              </div>
              <div className="space-y-2">
                <span className="text-[9px] text-accent-success uppercase font-black tracking-widest flex items-center gap-2">
                  <CheckCircle2 className="w-3 h-3" /> Forensic_Conclusion
                </span>
                <p className="text-xs text-accent-success font-bold leading-relaxed uppercase tracking-tight">
                  {step.conclusion}
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      ))}
      
      {/* End of Chain Indicator */}
      <div className="pl-10">
        <div className="h-px w-full bg-gradient-to-r from-amd-gray-800 to-transparent" />
        <p className="text-[9px] font-mono text-amd-gray-700 mt-2 uppercase tracking-[0.5em]">END_OF_REASONING_CHAIN</p>
      </div>
    </div>
  );
};
