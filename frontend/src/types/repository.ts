export interface CommitInfo {
  sha: string
  shortSha: string
  author: string
  message: string
  timestamp: string
  branch?: string
  filesChanged?: number
  insertions?: number
  deletions?: number
}

export interface RepositoryState {
  url: string
  name: string
  defaultBranch: string
  baseCommit: CommitInfo
  headCommit: CommitInfo
  availableBranches: string[]
  recentCommits: CommitInfo[]
}
