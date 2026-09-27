import React, { useState } from 'react'
import {
  Wrench,
  ShieldCheck,
  CheckCircle,
  XCircle,
  Download,
  RotateCcw,
  FileCode,
  AlertTriangle,
  FileCheck,
  Copy,
  Check,
} from 'lucide-react'
import { useRepairStore } from '../../store'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './RepairStudio.css'

export interface RepairStudioProps {
  onNavigateToExport?: () => void
}

export const RepairStudio: React.FC<RepairStudioProps> = ({ onNavigateToExport }) => {
  const { repair, approveRepair, rejectRepair } = useRepairStore()
  const [copiedPatch, setCopiedPatch] = useState(false)
  const [viewMode, setViewMode] = useState<'unified' | 'plan'>('unified')

  const handleCopyPatch = () => {
    navigator.clipboard.writeText(repair.patchContent)
    setCopiedPatch(true)
    setTimeout(() => setCopiedPatch(false), 2000)
  }

  const handleDownloadPatch = () => {
    const blob = new Blob([repair.patchContent], { type: 'text/x-diff' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `repair-${repair.targetFunction}.patch`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="sd-repair-studio animate-fade-in">
      <SectionHeader
        title="IBM Bob AI Repair Studio"
        subtitle="Autonomous patch synthesizer converts root cause intelligence into verified Git unified diffs with safety validation and rollback procedures."
        icon={<Wrench size={20} />}
        actions={
          <div className="sd-repair-studio__top-actions">
            <Button
              variant="outline"
              size="sm"
              icon={copiedPatch ? <Check size={14} /> : <Copy size={14} />}
              onClick={handleCopyPatch}
            >
              {copiedPatch ? 'Copied Diff!' : 'Copy Patch'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={<Download size={14} />}
              onClick={handleDownloadPatch}
            >
              Export .patch
            </Button>
            {repair.status === 'approved' ? (
              <>
                <Badge severity="SUCCESS" size="md">
                  <CheckCircle size={14} /> Approved & Ready for PR
                </Badge>
                {onNavigateToExport && (
                  <Button variant="cyan" size="sm" onClick={onNavigateToExport}>
                    Go to Export Center →
                  </Button>
                )}
              </>
            ) : repair.status === 'rejected' ? (
              <Badge severity="CRITICAL" size="md">
                <XCircle size={14} /> Rejected by Developer
              </Badge>
            ) : (
              <>
                <Button variant="danger" size="sm" onClick={rejectRepair}>
                  Reject
                </Button>
                <Button variant="cyan" size="sm" icon={<CheckCircle size={14} />} onClick={approveRepair}>
                  Approve Repair
                </Button>
              </>
            )}
          </div>
        }
      />

      {/* Target & Risk Summary Bar */}
      <div className="sd-repair-bar-grid">
        <Card variant="glass" className="sd-repair-target-card">
          <CardContent>
            <div className="sd-repair-target-row">
              <FileCode size={20} className="text-cyan" />
              <div className="sd-repair-target-meta">
                <span className="label">Target Module</span>
                <span className="file-name">{repair.targetFile}</span>
                <span className="func-name">Function: <code>{repair.targetFunction}()</code></span>
              </div>
              <div className="sd-repair-status-pill">
                <Badge
                  severity={
                    repair.status === 'approved'
                      ? 'SUCCESS'
                      : repair.status === 'rejected'
                      ? 'CRITICAL'
                      : 'INFO'
                  }
                  size="md"
                >
                  STATUS: {repair.status.toUpperCase()}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Risk Assessment Score Card */}
        <Card variant="glass" className="sd-repair-risk-card">
          <CardContent>
            <div className="sd-repair-risk-row">
              <AlertTriangle size={20} className="text-warning" />
              <div className="sd-repair-risk-info">
                <span className="label">Operational Risk Assessment</span>
                <div className="sd-repair-risk-score">
                  <span className="score-val">{repair.risk.score}/100</span>
                  <Badge severity={repair.risk.level} size="sm">{repair.risk.level} TIER</Badge>
                </div>
              </div>
            </div>
            <div className="sd-repair-risk-reasons">
              {repair.risk.reasons.map((r, i) => (
                <span key={i} className="sd-risk-bullet">• {r}</span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* View Switcher: Diff vs Action Plan */}
      <div className="sd-repair-view-switch">
        <button
          className={`sd-view-btn ${viewMode === 'unified' ? 'is-active' : ''}`}
          onClick={() => setViewMode('unified')}
        >
          <FileCode size={14} /> Git Unified Diff (.patch)
        </button>
        <button
          className={`sd-view-btn ${viewMode === 'plan' ? 'is-active' : ''}`}
          onClick={() => setViewMode('plan')}
        >
          <FileCheck size={14} /> Repair Action Plan ({repair.planActions.length} steps)
        </button>
      </div>

      {/* Main Diff / Plan Viewer */}
      {viewMode === 'unified' ? (
        <Card className="sd-diff-viewer-card">
          <CardHeader>
            <CardTitle>
              <FileCode size={16} /> Patch Preview: {repair.targetFile}
            </CardTitle>
            <div className="sd-diff-stats">
              <span className="stat-add">+6 additions</span>
              <span className="stat-del">-2 deletions</span>
            </div>
          </CardHeader>
          <CardContent className="sd-diff-viewer-body">
            <div className="sd-diff-code-window">
              {repair.patchContent.split('\n').map((line, idx) => {
                const isAdd = line.startsWith('+') && !line.startsWith('+++')
                const isDel = line.startsWith('-') && !line.startsWith('---')
                const isHeader = line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')

                return (
                  <div
                    key={idx}
                    className={`sd-diff-line ${isAdd ? 'is-add' : isDel ? 'is-del' : isHeader ? 'is-header' : ''}`}
                  >
                    <span className="sd-diff-line-num">{idx + 1}</span>
                    <span className="sd-diff-line-content">{line}</span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="sd-plan-card">
          <CardHeader>
            <CardTitle>
              <FileCheck size={16} /> Synthesized Repair Execution Steps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="sd-plan-steps-list">
              {repair.planActions.map((act) => (
                <div key={act.step} className="sd-plan-step-item">
                  <div className="sd-plan-step-num">Step {act.step}</div>
                  <div className="sd-plan-step-body">
                    <span className="sd-plan-step-desc">{act.description}</span>
                    <span className="sd-plan-step-type font-mono">[{act.actionType}]</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Verification & Rollback Bottom Grid */}
      <div className="sd-repair-bottom-grid">
        {/* Safety Gate Checklist */}
        <Card>
          <CardHeader>
            <CardTitle>
              <ShieldCheck size={16} className="text-cyan" /> Pre-Flight Safety Verification
            </CardTitle>
            <Badge severity="SUCCESS" size="sm">PASSED</Badge>
          </CardHeader>
          <CardContent>
            <div className="sd-safety-notes-list">
              {repair.safety.notes.map((note, idx) => (
                <div key={idx} className="sd-safety-note-item">
                  <CheckCircle size={14} className="text-success" />
                  <span>{note}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Safe Rollback Procedures */}
        <Card>
          <CardHeader>
            <CardTitle>
              <RotateCcw size={16} className="text-warning" /> Safe Rollback Procedures
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="sd-rollback-procedures">
              <div className="sd-rollback-cmd-box">
                <span className="label">1-Click Reverse Command:</span>
                <code>{repair.rollback.gitApplyReverse}</code>
              </div>
              <ul className="sd-rollback-list">
                {repair.rollback.steps.map((st, idx) => (
                  <li key={idx}>{st}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
