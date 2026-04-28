import { Severity } from "@/types/atlas";
import { cn } from "@/lib/utils";

interface SeverityBadgeProps {
  severity: Severity | string;
  className?: string;
}

const SEVERITY_MAP: Record<string, { label: string; classes: string }> = {
  // English (Pipeline)
  CRITICAL: { label: "CRITICAL", classes: "bg-amd-red/10 text-amd-red border-amd-red/30 shadow-[0_0_10px_rgba(237,28,36,0.2)]" },
  HIGH: { label: "HIGH_RISK", classes: "bg-accent-warning/10 text-accent-warning border-accent-warning/30" },
  MEDIUM: { label: "MEDIUM_RISK", classes: "bg-accent-warning/5 text-accent-warning/80 border-accent-warning/20" },
  LOW: { label: "LOW_RISK", classes: "bg-accent-data/10 text-accent-data border-accent-data/30" },
  NONE: { label: "SECURE", classes: "bg-accent-success/10 text-accent-success border-accent-success/30" },
  
  // Spanish (Supabase)
  "CRÍTICO": { label: "CRITICAL", classes: "bg-amd-red/10 text-amd-red border-amd-red/30 shadow-[0_0_10px_rgba(237,28,36,0.2)]" },
  "ALTO": { label: "HIGH_RISK", classes: "bg-accent-warning/10 text-accent-warning border-accent-warning/30" },
  "MEDIO": { label: "MEDIUM_RISK", classes: "bg-accent-warning/5 text-accent-warning/80 border-accent-warning/20" },
  "BAJO": { label: "LOW_RISK", classes: "bg-accent-data/10 text-accent-data border-accent-data/30" },
  "NINGUNO": { label: "SECURE", classes: "bg-accent-success/10 text-accent-success border-accent-success/30" },
};

export const SeverityBadge = ({ severity, className }: SeverityBadgeProps) => {
  const config = SEVERITY_MAP[severity?.toUpperCase()] || { 
    label: severity?.toUpperCase() || "UNKNOWN", 
    classes: "bg-amd-gray-800 text-amd-gray-400 border-amd-gray-700" 
  };

  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          "px-2 py-0.5 rounded-sm text-[10px] font-mono font-black border uppercase tracking-widest transition-all",
          config.classes,
          className
        )}
      >
        {config.label}
      </span>
      {severity?.toUpperCase() === "CRITICAL" && (
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amd-red opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amd-red"></span>
        </span>
      )}
    </div>
  );
};
