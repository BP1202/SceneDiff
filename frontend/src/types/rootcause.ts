import { SeverityLevel } from './comparison'

export interface EvidenceNode {
  id: string
  label: string
  category: 'commit' | 'code' | 'dom' | 'network' | 'console' | 'storage'
  severity?: SeverityLevel
  description: string
  metadata?: Record<string, unknown>
}

export interface EvidenceEdge {
  id: string
  source: string
  target: string
  relation: string
  weight: number
}

export interface CandidateItem {
  file: string
  functionName: string
  lineStart: number
  lineEnd: number
  score: number
  rationale: string
  isPrimary: boolean
}

export interface RootCauseReport {
  id: string
  comparisonId: string
  primaryCandidate: CandidateItem
  secondaryCandidates: CandidateItem[]
  rootCauseConfidence: number // 0-100
  repairConfidence: number // 0-100
  explanation: string
  repairRecommendation: string
  evidenceNodes: EvidenceNode[]
  evidenceEdges: EvidenceEdge[]
  createdAt: string
}
