import { useQuery } from "@tanstack/react-query";
import { atlasApi } from "@/services/api";

export function useAtlasStats() {
  return useQuery({
    queryKey: ["atlas-stats"],
    queryFn: atlasApi.getStats,
    refetchInterval: 30_000,
    retry: 1,
  });
}
