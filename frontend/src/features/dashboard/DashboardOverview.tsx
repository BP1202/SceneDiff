import React from 'react'
import {
  Activity,
  AlertOctagon,
  BrainCircuit,
  Wrench,
  Play,
  ArrowRight,
  Layers,
  Globe,
  ShieldCheck,
  CheckCircle,
} from 'lucide-react'
import { useRepositoryStore, useComparisonStore, useRootCauseStore, useRepairStore } from '../../store'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { MetricCard } from '../../components/ui/MetricCard'
import { SectionHeader } from '../../components/ui/SectionHeader'
import { NavView } from '../../components/layouts/Sidebar'
import './DashboardOverview.css'

export interface DashboardOverviewProps {
  onNavigate: (view: NavView) => void
  onRunRuntime: () => void
  isRunningRuntime: boolean
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  onNavigate,
  onRunRuntime,
  isRunningRuntime,
}) => {
  const { repository } = useRepositoryStore()
  const { summary } = useComparisonStore()
  const { report } = useRootCauseStore()
  const { repair } = useRepairStore()

  const firstDivergence = summary.timeline.find((t) => t.isFirstDivergence)

  return (
    <div className="sd-dashboard animate-fade-in">
      <SectionHeader
        title="IBM Bob 2.0 Autonomous Debugging Workspace"
        subtitle={`Active Analysis for ${repository.name} (${repository.baseCommit.shortSha} → ${repository.headCommit.shortSha})`}
        icon={<Activity size={20} />}
        actions={
          <Button
            variant="cyan"
            size="sm"
            icon={<Play size={14} />}
            isLoading={isRunningRuntime}
            onClick={onRunRuntime}
          >
            {isRunningRuntime ? 'Collecting Traces...' : 'Run Runtime Collector'}
          </Button>
        }
      />

      {/* Top 4 Key Metric Cards */}
      <div className="sd-dashboard__metrics-grid">
        <MetricCard
          title="Runtime Divergence"
          value={`Step #${summary.divergenceStep}`}
          subtext="First meaningful behavior break"
          icon={<AlertOctagon size={18} />}
          accentColor="critical"
        />
        <MetricCard
          title="Regressions Found"
          value={`${summary.severityCounts.CRITICAL + summary.severityCounts.HIGH}`}
          subtext={`${summary.severityCounts.CRITICAL} Critical, ${summary.severityCounts.HIGH} High`}
          icon={<Activity size={18} />}
          accentColor="warning"
        />
        <MetricCard
          title="Root Cause Confidence"
          value={`${report.rootCauseConfidence}%`}
          subtext="Deterministic causal correlation"
          icon={<BrainCircuit size={18} />}
          accentColor="success"
        />
        <MetricCard
          title="Repair Confidence"
          value={`${report.repairConfidence}%`}
          subtext="AST & Secret Shield verified"
          icon={<Wrench size={18} />}
          accentColor="cyan"
        />
      </div>

      {/* Spotlight: First Divergence & Culprit Breakdown */}
      <div className="sd-dashboard__spotlight-grid">
        {/* Left: First Meaningful Runtime Divergence */}
        <Card variant="glass" className="sd-dashboard__spotlight-card is-divergence glow-critical">
          <CardHeader>
            <div className="sd-spotlight-header">
              <div className="sd-spotlight-title-row">
                <AlertOctagon size={18} className="text-danger" />
                <CardTitle>First Meaningful Runtime Divergence</CardTitle>
              </div>
              <Badge severity="CRITICAL" size="sm" dot glow>STEP #{summary.divergenceStep}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <h4 className="sd-spotlight-event-title">{firstDivergence?.title}</h4>
            <p className="sd-spotlight-desc">{firstDivergence?.description}</p>

            <div className="sd-spotlight-meta-box">
              <div className="meta-item">
                <span className="label">Endpoint:</span>
                <code className="text-cyan">{firstDivergence?.route}</code>
              </div>
              <div className="meta-item">
                <span className="label">Timestamp:</span>
                <code>{firstDivergence?.timestamp}</code>
              </div>
              <div className="meta-item">
                <span className="label">Symptom:</span>
                <span className="text-danger font-semibold">200 OK ➔ 500 Internal Server Error</span>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              iconRight={<ArrowRight size={14} />}
              onClick={() => onNavigate('comparison')}
              className="sd-spotlight-btn"
            >
              Inspect Divergence Timeline
            </Button>
          </CardContent>
        </Card>

        {/* Right: Culprit Code & Proposed Repair */}
        <Card variant="glass" className="sd-dashboard__spotlight-card is-repair glow-cyan">
          <CardHeader>
            <div className="sd-spotlight-header">
              <div className="sd-spotlight-title-row">
                <Wrench size={18} className="text-cyan" />
                <CardTitle>AI Repair Recommendation</CardTitle>
              </div>
              <Badge severity={repair.risk.level} size="sm">{repair.risk.level} RISK</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="sd-spotlight-culprit-pill">
              <code>{report.primaryCandidate.file}</code>
              <span className="divider">➔</span>
              <code className="func text-cyan">{report.primaryCandidate.functionName}()</code>
            </div>

            <p className="sd-spotlight-desc">{repair.summary}</p>

            <div className="sd-spotlight-safety-checks">
              <span className="safety-item">
                <CheckCircle size={13} className="text-success" /> AST Validation Passed
              </span>
              <span className="safety-item">
                <ShieldCheck size={13} className="text-success" /> Secret Shield (0 leaks)
              </span>
              <span className="safety-item">
                <CheckCircle size={13} className="text-success" /> Single File Scope
              </span>
            </div>

            <Button
              variant="cyan"
              size="sm"
              iconRight={<ArrowRight size={14} />}
              onClick={() => onNavigate('repair')}
              className="sd-spotlight-btn"
            >
              Review Proposed Git Patch
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick Navigation Cards Grid */}
      <div className="sd-dashboard__nav-cards">
        <Card variant="interactive" onClick={() => onNavigate('runtime')} className="sd-nav-shortcut">
          <CardContent>
            <div className="sd-nav-shortcut__content">
              <div className="sd-nav-shortcut__icon is-runtime"><Play size={18} /></div>
              <div>
                <h5 className="sd-nav-shortcut__title">Runtime Collector</h5>
                <p className="sd-nav-shortcut__sub">Playwright headless trace replay</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card variant="interactive" onClick={() => onNavigate('comparison')} className="sd-nav-shortcut">
          <CardContent>
            <div className="sd-nav-shortcut__content">
              <div className="sd-nav-shortcut__icon is-timeline"><Layers size={18} /></div>
              <div>
                <h5 className="sd-nav-shortcut__title">DOM & Visual Diff</h5>
                <p className="sd-nav-shortcut__sub">Mutation tree and UI states</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card variant="interactive" onClick={() => onNavigate('comparison')} className="sd-nav-shortcut">
          <CardContent>
            <div className="sd-nav-shortcut__content">
              <div className="sd-nav-shortcut__icon is-network"><Globe size={18} /></div>
              <div>
                <h5 className="sd-nav-shortcut__title">Network Inspector</h5>
                <p className="sd-nav-shortcut__sub">API regressions & latency</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card variant="interactive" onClick={() => onNavigate('rootcause')} className="sd-nav-shortcut">
          <CardContent>
            <div className="sd-nav-shortcut__content">
              <div className="sd-nav-shortcut__icon is-rootcause"><BrainCircuit size={18} /></div>
              <div>
                <h5 className="sd-nav-shortcut__title">Causal Evidence Graph</h5>
                <p className="sd-nav-shortcut__sub">Interactive DAG root cause</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
