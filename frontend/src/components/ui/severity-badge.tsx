import { Severity } from "@/types/atlas";
import { cn } from "@/lib/utils";

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

const SEVERITY_CONFIG = {
  CRITICAL: "bg-red-500/10 text-red-500 border-red-500/20",
  HIGH: "bg-orange-500/10 text-orange-500 border-orange-500/20",
  MEDIUM: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
  LOW: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  NONE: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
} as const;

export const SeverityBadge = ({ severity, className }: SeverityBadgeProps) => {
  return (
    <span
      className={cn(
        "px-2.5 py-0.5 rounded-full text-xs font-bold border tracking-wider",
        SEVERITY_CONFIG[severity] || "bg-gray-500/10 text-gray-500 border-gray-500/20",
        className
      )}
    >
      {severity}
    </span>
  );
};
