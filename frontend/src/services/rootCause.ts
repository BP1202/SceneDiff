import { apiClient, ApiResponse } from './api'
import { RootCauseReport } from '../types'
import { mockRootCauseReport } from '../utils/mockData'

export async function createRootCauseAnalysis(comparisonId: string): Promise<RootCauseReport> {
  try {
    const res = await apiClient<ApiResponse<RootCauseReport>>('/root-causes', {
      method: 'POST',
      body: JSON.stringify({ comparison_id: comparisonId }),
    })
    return res.data
  } catch {
    return mockRootCauseReport
  }
}

export async function getRootCauseReport(id: string): Promise<RootCauseReport> {
  try {
    const res = await apiClient<ApiResponse<RootCauseReport>>(`/root-causes/${id}`)
    return res.data
  } catch {
    return mockRootCauseReport
  }
}
