import { SeverityLevel } from './comparison'

export interface RepairActionStep {
  step: number
  description: string
  actionType: 'inspect' | 'null_guard' | 'exception_raise' | 'caller_update' | 'custom'
}

export interface RepairPatchSafety {
  isValid: boolean
  syntaxValid: boolean
  astPassed: boolean
  secretScanPassed: boolean
  scopeVerified: boolean
  notes: string[]
}

export interface RepairRiskAssessment {
  level: SeverityLevel
  score: number // 0-100
  reasons: string[]
  isSensitiveModule: boolean
  linesChanged: number
}

export interface RollbackPlan {
  gitApplyReverse: string
  gitRevert: string
  steps: string[]
  hasDatabaseCaution: boolean
}

export interface RepairReportData {
  id: string
  rootCauseId: string
  comparisonId: string
  summary: string
  targetFile: string
  targetFunction: string
  patchContent: string
  planActions: RepairActionStep[]
  safety: RepairPatchSafety
  risk: RepairRiskAssessment
  rollback: RollbackPlan
  status: 'proposed' | 'approved' | 'rejected' | 'exported'
  createdAt: string
}
