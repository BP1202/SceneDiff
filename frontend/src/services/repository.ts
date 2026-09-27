import { apiClient, ApiResponse } from './api'
import { CommitInfo, RepositoryState } from '../types'
import { mockRepository } from '../utils/mockData'

export async function fetchRepositoryInfo(): Promise<RepositoryState> {
  try {
    const res = await apiClient<ApiResponse<RepositoryState>>('/repository')
    return res.data
  } catch {
    // Return mock data for offline/standalone demo mode
    return mockRepository
  }
}

export async function fetchCommits(): Promise<CommitInfo[]> {
  try {
    const res = await apiClient<ApiResponse<CommitInfo[]>>('/repository/commits')
    return res.data
  } catch {
    return mockRepository.recentCommits
  }
}
