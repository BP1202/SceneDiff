import { apiClient, ApiResponse } from './api'
import { RuntimeExecution } from '../types'
import { mockRuntimeExecution } from '../utils/mockData'

export interface CollectRuntimePayload {
  url: string
  commitSha: string
  routes?: string[]
}

export async function triggerRuntimeCollection(payload: CollectRuntimePayload): Promise<RuntimeExecution> {
  try {
    const res = await apiClient<ApiResponse<RuntimeExecution>>('/runtime/collect', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return res.data
  } catch {
    return mockRuntimeExecution
  }
}

export async function getRuntimeStatus(executionId: string): Promise<RuntimeExecution> {
  try {
    const res = await apiClient<ApiResponse<RuntimeExecution>>(`/runtime/status/${executionId}`)
    return res.data
  } catch {
    return mockRuntimeExecution
  }
}
