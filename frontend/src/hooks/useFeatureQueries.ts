import { useQuery } from '@tanstack/react-query'
import { getComparisonSummary } from '../services/comparison'
import { getRootCauseReport } from '../services/rootCause'
import { getRepairReport, getRepairPatch } from '../services/repair'

export function useComparisonQuery(comparisonId: string) {
  return useQuery({
    queryKey: ['comparison', comparisonId],
    queryFn: () => getComparisonSummary(comparisonId),
    staleTime: 1000 * 60 * 5,
    enabled: Boolean(comparisonId),
  })
}

export function useRootCauseQuery(rootCauseId: string) {
  return useQuery({
    queryKey: ['rootCause', rootCauseId],
    queryFn: () => getRootCauseReport(rootCauseId),
    staleTime: 1000 * 60 * 5,
    enabled: Boolean(rootCauseId),
  })
}

export function useRepairQuery(repairId: string) {
  return useQuery({
    queryKey: ['repair', repairId],
    queryFn: () => getRepairReport(repairId),
    staleTime: 1000 * 60 * 5,
    enabled: Boolean(repairId),
  })
}

export function useRepairPatchQuery(repairId: string) {
  return useQuery({
    queryKey: ['repairPatch', repairId],
    queryFn: () => getRepairPatch(repairId),
    staleTime: 1000 * 60 * 5,
    enabled: Boolean(repairId),
  })
}
