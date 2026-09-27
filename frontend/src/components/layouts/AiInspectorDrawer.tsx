import React from 'react'
import {
  Sparkles,
  X,
  FileCode,
  ShieldAlert,
  ArrowUpRight,
  CheckCircle,
  Lightbulb,
} from 'lucide-react'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import './AiInspectorDrawer.css'

export interface AiInspectorDrawerProps {
  isOpen: boolean
  onClose: () => void
  onNavigateToRepair: () => void
  onNavigateToRootCause: () => void
  divergenceStep?: number
  culpritFile?: string
  culpritFunction?: string
  confidenceScore?: number
  riskLevel?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'INFO'
}

export const AiInspectorDrawer: React.FC<AiInspectorDrawerProps> = ({
  isOpen,
  onClose,
  onNavigateToRepair,
  onNavigateToRootCause,
  divergenceStep = 3,
  culpritFile = 'app/auth/login.py',
  culpritFunction = 'validate_token',
  confidenceScore = 94,
  riskLevel = 'HIGH',
}) => {
  if (!isOpen) return null

  return (
    <aside className="sd-ai-drawer animate-fade-in">
      <div className="sd-ai-drawer__header">
        <div className="sd-ai-drawer__title-row">
          <div className="sd-ai-drawer__icon-badge">
            <Sparkles size={16} />
          </div>
          <div>
            <h3 className="sd-ai-drawer__title">IBM Bob 2.0</h3>
            <span className="sd-ai-drawer__subtitle">Autonomous Repair Agent</span>
          </div>
        </div>
        <button className="sd-ai-drawer__close" onClick={onClose} aria-label="Close drawer">
          <X size={16} />
        </button>
      </div>

      <div className="sd-ai-drawer__body">
        {/* Active Analysis Insight */}
        <div className="sd-ai-drawer__card glass-panel">
          <div className="sd-ai-drawer__card-header">
            <Lightbulb size={15} className="sd-ai-drawer__accent-icon" />
            <span className="sd-ai-drawer__card-title">Behavior Divergence Detected</span>
            <Badge severity="CRITICAL" size="sm">Step #{divergenceStep}</Badge>
          </div>
          <p className="sd-ai-drawer__card-desc">
            First meaningful runtime divergence occurred during authentication payload parsing.
            Response status switched from <code>200 OK</code> to <code>500 Internal Error</code>.
          </p>
        </div>

        {/* Root Cause Candidate */}
        <div className="sd-ai-drawer__card">
          <div className="sd-ai-drawer__card-header">
            <FileCode size={15} className="sd-ai-drawer__accent-icon" />
            <span className="sd-ai-drawer__card-title">Culprit Candidate</span>
            <Badge severity="INFO" size="sm">{confidenceScore}% Confidence</Badge>
          </div>
          <div className="sd-ai-drawer__code-pill">
            <span className="sd-ai-drawer__file-name">{culpritFile}</span>
            <code className="sd-ai-drawer__func-name">{culpritFunction}()</code>
          </div>
          <p className="sd-ai-drawer__card-desc">
            <code>validate_token()</code> returns <code>None</code> for expired JWT tokens,
            triggering downstream <code>AttributeError</code> during role check.
          </p>
          <Button
            variant="outline"
            size="sm"
            iconRight={<ArrowUpRight size={14} />}
            onClick={onNavigateToRootCause}
            className="sd-ai-drawer__card-btn"
          >
            Explore Evidence Graph
          </Button>
        </div>

        {/* Repair Proposal */}
        <div className="sd-ai-drawer__card">
          <div className="sd-ai-drawer__card-header">
            <ShieldAlert size={15} className="sd-ai-drawer__accent-icon" />
            <span className="sd-ai-drawer__card-title">Generated Repair Patch</span>
            <Badge severity={riskLevel} size="sm">{riskLevel} Risk</Badge>
          </div>
          <ul className="sd-ai-drawer__checklist">
            <li>
              <CheckCircle size={13} className="sd-ai-drawer__check-icon" />
              <span>AST Syntax Check Passed</span>
            </li>
            <li>
              <CheckCircle size={13} className="sd-ai-drawer__check-icon" />
              <span>Secret Shield Scanned (0 leaks)</span>
            </li>
            <li>
              <CheckCircle size={13} className="sd-ai-drawer__check-icon" />
              <span>Scope Verified: strictly 1 culprit file</span>
            </li>
          </ul>
          <Button
            variant="cyan"
            size="sm"
            iconRight={<ArrowUpRight size={14} />}
            onClick={onNavigateToRepair}
            className="sd-ai-drawer__card-btn"
          >
            Review & Approve Patch
          </Button>
        </div>
      </div>
    </aside>
  )
}
