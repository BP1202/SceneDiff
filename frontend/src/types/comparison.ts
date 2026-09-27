export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'

export type DiffCategory = 'dom' | 'network' | 'console' | 'storage' | 'performance'

export interface TimelineEvent {
  id: string
  timestamp: string
  stepIndex: number
  category: DiffCategory
  severity: SeverityLevel
  title: string
  description: string
  route: string
  evidenceCount: number
  isFirstDivergence?: boolean
  details?: Record<string, unknown>
}

export interface DOMDiffItem {
  id: string
  selector: string
  changeType: 'added' | 'removed' | 'modified' | 'attribute_changed'
  baseValue?: string
  headValue?: string
  xpath: string
  severity: SeverityLevel
}

export interface NetworkDiffItem {
  id: string
  url: string
  method: string
  baseStatus?: number
  headStatus?: number
  baseLatencyMs?: number
  headLatencyMs?: number
  severity: SeverityLevel
  isRegression: boolean
  errorDetail?: string
}

export interface ConsoleDiffItem {
  id: string
  type: 'error' | 'warn' | 'info' | 'unhandled_rejection'
  message: string
  stackTrace?: string
  occurrence: 'new' | 'resolved' | 'existing'
  severity: SeverityLevel
}

export interface StorageDiffItem {
  key: string
  storageType: 'localStorage' | 'sessionStorage' | 'cookie'
  baseValue?: string
  headValue?: string
  isSecretMasked: boolean
  changeType: 'added' | 'removed' | 'modified'
}

export interface PerformanceMetricDiff {
  metric: 'FCP' | 'LCP' | 'TTFB' | 'DOM_Interactive' | 'JS_Heap'
  unit: 'ms' | 'MB'
  baseValue: number
  headValue: number
  deltaPercent: number
  severity: SeverityLevel
}

export interface BehaviorComparisonSummary {
  id: string
  baseCommit: string
  headCommit: string
  divergenceStep: number
  totalDifferences: number
  severityCounts: Record<SeverityLevel, number>
  timeline: TimelineEvent[]
  domDiffs: DOMDiffItem[]
  networkDiffs: NetworkDiffItem[]
  consoleDiffs: ConsoleDiffItem[]
  storageDiffs: StorageDiffItem[]
  performanceDiffs: PerformanceMetricDiff[]
}
