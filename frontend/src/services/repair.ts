import { apiClient, ApiResponse } from './api'
import { RepairReportData } from '../types'
import { mockRepairReport } from '../utils/mockData'

export async function createRepair(rootCauseId: string): Promise<RepairReportData> {
  try {
    const res = await apiClient<ApiResponse<RepairReportData>>('/repairs', {
      method: 'POST',
      body: JSON.stringify({ root_cause_id: rootCauseId }),
    })
    return res.data
  } catch {
    return mockRepairReport
  }
}

export async function getRepairReport(id: string): Promise<RepairReportData> {
  try {
    const res = await apiClient<ApiResponse<RepairReportData>>(`/repairs/${id}`)
    return res.data
  } catch {
    return mockRepairReport
  }
}

export async function getRepairPatch(id: string): Promise<string> {
  try {
    const patch = await apiClient<string>(`/repairs/${id}/patch`)
    return patch
  } catch {
    return mockRepairReport.patchContent
  }
}
