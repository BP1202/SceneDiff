import React, { useState } from 'react'
import {
  Play,
  RotateCcw,
  CheckCircle2,
  Terminal,
  Layers,
  Globe,
  Database,
  Activity,
  ShieldCheck,
  StopCircle,
} from 'lucide-react'
import { useRuntimeStore } from '../../store'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { MetricCard } from '../../components/ui/MetricCard'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './RuntimeCollector.css'

export interface RuntimeCollectorProps {
  onNavigateToComparison?: () => void
}

export const RuntimeCollector: React.FC<RuntimeCollectorProps> = ({ onNavigateToComparison }) => {
  const { execution, isRunning, startExecution, finishExecution, reset } = useRuntimeStore()
  const [filterPhase, setFilterPhase] = useState<string>('all')

  const handleSimulateRun = () => {
    startExecution()
    setTimeout(() => {
      finishExecution()
    }, 1200)
  }

  const filteredLogs = filterPhase === 'all'
    ? execution.logs
    : execution.logs.filter((l) => l.phase === filterPhase)

  return (
    <div className="sd-runtime-collector animate-fade-in">
      <SectionHeader
        title="Playwright Runtime Trace Collector"
        subtitle="Spawns headless Chromium to execute commits, capture DOM mutations, network payloads, console messages, and storage under Secret Shield."
        icon={<Play size={20} />}
        badge={
          <Badge severity={isRunning ? 'INFO' : 'SUCCESS'} dot glow={isRunning}>
            {isRunning ? 'Execution In Progress' : 'Ready'}
          </Badge>
        }
        actions={
          <div className="sd-runtime-collector__actions">
            <Button
              variant="outline"
              size="sm"
              icon={<RotateCcw size={14} />}
              onClick={reset}
              disabled={isRunning}
            >
              Reset Logs
            </Button>
            {isRunning ? (
              <Button
                variant="danger"
                size="sm"
                icon={<StopCircle size={14} />}
                onClick={finishExecution}
              >
                Abort Run
              </Button>
            ) : (
              <Button
                variant="cyan"
                size="sm"
                icon={<Play size={14} />}
                onClick={handleSimulateRun}
              >
                Run Collector
              </Button>
            )}
            {execution.status === 'completed' && onNavigateToComparison && (
              <Button variant="primary" size="sm" onClick={onNavigateToComparison}>
                View Behavior Diff →
              </Button>
            )}
          </div>
        }
      />

      {/* Real-time Collector Metrics */}
      <div className="sd-runtime-collector__metrics-grid">
        <MetricCard
          title="Execution Duration"
          value={isRunning ? 'Running...' : `${execution.durationMs}ms`}
          subtext="Headless Chromium runtime"
          icon={<Activity size={18} />}
          accentColor="cyan"
        />
        <MetricCard
          title="DOM Nodes Indexed"
          value={execution.domNodesCaptured}
          subtext="Interactive element snapshots"
          icon={<Layers size={18} />}
          accentColor="primary"
        />
        <MetricCard
          title="Network Invocations"
          value={execution.networkRequestsCaptured}
          subtext="XHR, Fetch & API calls"
          icon={<Globe size={18} />}
          accentColor="warning"
        />
        <MetricCard
          title="Storage & Console"
          value={`${execution.consoleMessagesCaptured} errs / ${execution.storageKeysCaptured} keys`}
          subtext="Secrets auto-masked"
          icon={<Database size={18} />}
          accentColor="success"
        />
      </div>

      {/* Status Phase Tracker */}
      <Card className="sd-runtime-collector__stepper-card">
        <CardContent>
          <div className="sd-runtime-collector__stepper">
            {[
              { id: 'browser', label: '1. Launch Chromium', active: isRunning || execution.status === 'completed' },
              { id: 'navigation', label: '2. Route Navigation', active: isRunning || execution.status === 'completed' },
              { id: 'dom', label: '3. DOM & Visual Capture', active: isRunning || execution.status === 'completed' },
              { id: 'network', label: '4. Network & Storage', active: isRunning || execution.status === 'completed' },
              { id: 'complete', label: '5. Secret Shield Normalize', active: execution.status === 'completed' },
            ].map((step, idx) => (
              <div
                key={step.id}
                className={`sd-runtime-stepper__step ${step.active ? 'is-active' : ''} ${step.active && !isRunning ? 'is-done' : ''}`}
              >
                <div className="sd-runtime-stepper__icon">
                  {step.active && !isRunning ? <CheckCircle2 size={16} /> : <span>{idx + 1}</span>}
                </div>
                <span className="sd-runtime-stepper__label">{step.label}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Live Trace Logs Terminal */}
      <Card className="sd-runtime-collector__terminal-card">
        <CardHeader>
          <CardTitle>
            <Terminal size={16} /> Live Playwright Trace Logs
          </CardTitle>
          <div className="sd-runtime-collector__terminal-filters">
            <span className="sd-runtime-collector__shield-tag">
              <ShieldCheck size={13} /> Secret Shield Enabled
            </span>
            <select
              className="sd-runtime-collector__select"
              value={filterPhase}
              onChange={(e) => setFilterPhase(e.target.value)}
            >
              <option value="all">All Phases</option>
              <option value="browser">Browser</option>
              <option value="navigation">Navigation</option>
              <option value="dom">DOM</option>
              <option value="network">Network</option>
              <option value="console">Console</option>
              <option value="storage">Storage</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="sd-runtime-collector__terminal-body">
          <div className="sd-runtime-terminal">
            {filteredLogs.map((log) => (
              <div key={log.id} className={`sd-runtime-terminal__row is-${log.level}`}>
                <span className="sd-runtime-terminal__time">[{log.timestamp}]</span>
                <span className={`sd-runtime-terminal__badge is-${log.level}`}>
                  {log.level.toUpperCase()}
                </span>
                {log.phase && (
                  <span className="sd-runtime-terminal__phase">[{log.phase}]</span>
                )}
                <span className="sd-runtime-terminal__msg">{log.message}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
