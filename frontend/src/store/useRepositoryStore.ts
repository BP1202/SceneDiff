import { create } from 'zustand'
import { RepositoryState, CommitInfo } from '../types'
import { mockRepository } from '../utils/mockData'

interface RepositoryStoreState {
  repository: RepositoryState
  setRepositoryUrl: (url: string) => void
  setBaseCommit: (commit: CommitInfo) => void
  setHeadCommit: (commit: CommitInfo) => void
  setTarget: (name: string, baseSha: string, headSha: string) => void
}

export const useRepositoryStore = create<RepositoryStoreState>((set) => ({
  repository: mockRepository,
  setRepositoryUrl: (url) =>
    set((state) => ({ repository: { ...state.repository, url } })),
  setBaseCommit: (commit) =>
    set((state) => ({ repository: { ...state.repository, baseCommit: commit } })),
  setHeadCommit: (commit) =>
    set((state) => ({ repository: { ...state.repository, headCommit: commit } })),
  setTarget: (name, baseSha, headSha) =>
    set((state) => ({
      repository: {
        ...state.repository,
        name,
        baseCommit: {
          ...state.repository.baseCommit,
          sha: baseSha,
          shortSha: baseSha.slice(0, 7),
        },
        headCommit: {
          ...state.repository.headCommit,
          sha: headSha,
          shortSha: headSha.slice(0, 7),
        },
      },
    })),
}))
