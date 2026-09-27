import { apiClient, ApiResponse } from './api'
import { BehaviorComparisonSummary } from '../types'
import { mockComparisonSummary } from '../utils/mockData'

export async function createComparison(baseCommit: string, headCommit: string): Promise<BehaviorComparisonSummary> {
  try {
    const res = await apiClient<ApiResponse<BehaviorComparisonSummary>>('/comparisons', {
      method: 'POST',
      body: JSON.stringify({ base_commit: baseCommit, head_commit: headCommit }),
    })
    return res.data
  } catch {
    return mockComparisonSummary
  }
}

export async function getComparisonSummary(id: string): Promise<BehaviorComparisonSummary> {
  try {
    const res = await apiClient<ApiResponse<BehaviorComparisonSummary>>(`/comparisons/${id}`)
    return res.data
  } catch {
    return mockComparisonSummary
  }
}
