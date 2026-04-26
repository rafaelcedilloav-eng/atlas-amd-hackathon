import { useQuery } from "@tanstack/react-query";
import { atlasApi } from "@/services/api";

export function useRecentAudits(limit = 10) {
  return useQuery({
    queryKey: ["recent-audits", limit],
    queryFn: () => atlasApi.getAudits(limit),
    refetchInterval: 15_000,
    retry: 1,
  });
}
