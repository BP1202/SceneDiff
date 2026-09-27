import { useQuery } from '@tanstack/react-query'
import { fetchRepositoryInfo, fetchCommits } from '../services/repository'

export function useRepositoryQuery() {
  return useQuery({
    queryKey: ['repository'],
    queryFn: fetchRepositoryInfo,
    staleTime: 1000 * 60 * 5,
  })
}

export function useCommitsQuery() {
  return useQuery({
    queryKey: ['commits'],
    queryFn: fetchCommits,
    staleTime: 1000 * 60 * 5,
  })
}
