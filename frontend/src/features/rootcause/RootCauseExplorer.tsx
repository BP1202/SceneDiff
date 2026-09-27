import React from 'react'
import {
  BrainCircuit,
  FileCode,
  ArrowRight,
  Sparkles,
  Wrench,
} from 'lucide-react'
import { useRootCauseStore } from '../../store'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './RootCauseExplorer.css'

export interface RootCauseExplorerProps {
  onNavigateToRepair?: () => void
  onToggleGraphView?: () => void
}

export const RootCauseExplorer: React.FC<RootCauseExplorerProps> = ({
  onNavigateToRepair,
  onToggleGraphView,
}) => {
  const { report } = useRootCauseStore()
  const { primaryCandidate, secondaryCandidates } = report

  return (
    <div className="sd-root-cause animate-fade-in">
      <SectionHeader
        title="AI Root Cause Intelligence Engine"
        subtitle="IBM Bob synthesized runtime behavior divergence events into an explainable code-level culprit with independent confidence scoring."
        icon={<BrainCircuit size={20} />}
        actions={
          <div className="sd-root-cause__top-actions">
            {onToggleGraphView && (
              <Button variant="outline" size="sm" onClick={onToggleGraphView}>
                View Evidence Graph
              </Button>
            )}
            {onNavigateToRepair && (
              <Button
                variant="cyan"
                size="sm"
                iconRight={<ArrowRight size={14} />}
                onClick={onNavigateToRepair}
              >
                Open Repair Studio
              </Button>
            )}
          </div>
        }
      />

      {/* Confidence Header Cards */}
      <div className="sd-root-cause__confidence-grid">
        <Card variant="glass" className="sd-confidence-card is-root">
          <CardContent>
            <div className="sd-confidence-row">
              <div className="sd-confidence-icon-wrap">
                <BrainCircuit size={24} />
              </div>
              <div className="sd-confidence-info">
                <span className="sd-confidence-label">Root Cause Confidence</span>
                <div className="sd-confidence-val">
                  <span>{report.rootCauseConfidence}%</span>
                  <Badge severity="SUCCESS" size="sm">CERTAIN</Badge>
                </div>
              </div>
            </div>
            <div className="sd-meter-track">
              <div
                className="sd-meter-fill is-root"
                style={{ width: `${report.rootCauseConfidence}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card variant="glass" className="sd-confidence-card is-repair">
          <CardContent>
            <div className="sd-confidence-row">
              <div className="sd-confidence-icon-wrap">
                <Wrench size={24} />
              </div>
              <div className="sd-confidence-info">
                <span className="sd-confidence-label">Repair Confidence</span>
                <div className="sd-confidence-val">
                  <span>{report.repairConfidence}%</span>
                  <Badge severity="INFO" size="sm">HIGH CONFIDENCE</Badge>
                </div>
              </div>
            </div>
            <div className="sd-meter-track">
              <div
                className="sd-meter-fill is-repair"
                style={{ width: `${report.repairConfidence}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Primary Culprit Candidate */}
      <Card variant="glass" className="sd-culprit-card glow-cyan">
        <CardHeader>
          <div className="sd-culprit-header">
            <div className="sd-culprit-title-row">
              <Sparkles size={18} className="text-cyan" />
              <CardTitle>Primary Culprit Candidate</CardTitle>
            </div>
            <Badge severity="CRITICAL" size="md" dot glow>
              SCORE: {(primaryCandidate.score * 100).toFixed(0)}%
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="sd-culprit-location">
            <div className="sd-culprit-pill">
              <FileCode size={15} />
              <span className="sd-culprit-file">{primaryCandidate.file}</span>
            </div>
            <div className="sd-culprit-func">
              Function: <code>{primaryCandidate.functionName}()</code> (Lines {primaryCandidate.lineStart}-{primaryCandidate.lineEnd})
            </div>
          </div>

          <div className="sd-culprit-rationale">
            <h5 className="sd-section-mini-title">Rationale:</h5>
            <p>{primaryCandidate.rationale}</p>
          </div>

          <div className="sd-culprit-explanation">
            <h5 className="sd-section-mini-title">Detailed Autonomous Analysis:</h5>
            <p>{report.explanation}</p>
          </div>

          <div className="sd-culprit-recommendation">
            <h5 className="sd-section-mini-title">Bob's Proposed Action:</h5>
            <p>{report.repairRecommendation}</p>
          </div>
        </CardContent>
      </Card>

      {/* Secondary Candidates */}
      {secondaryCandidates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              <FileCode size={16} /> Secondary Call-Site Candidates ({secondaryCandidates.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="sd-secondary-candidates-list">
              {secondaryCandidates.map((cand, idx) => (
                <div key={idx} className="sd-secondary-candidate-item">
                  <div className="sd-sec-cand-header">
                    <code>{cand.file} → {cand.functionName}()</code>
                    <Badge severity="MEDIUM" size="sm">Score: {(cand.score * 100).toFixed(0)}%</Badge>
                  </div>
                  <p className="sd-sec-cand-rationale">{cand.rationale}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
