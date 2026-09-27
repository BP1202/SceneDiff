import React from 'react'
import {
  GitCompare,
  AlertOctagon,
  Clock,
  Layers,
  Globe,
  Terminal,
  Database,
  ArrowRight,
  Filter,
} from 'lucide-react'
import { useComparisonStore } from '../../store'
import { DiffCategory, SeverityLevel, TimelineEvent } from '../../types'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './BehaviorTimeline.css'

export interface BehaviorTimelineProps {
  onSelectEvent?: (event: TimelineEvent) => void
  onNavigateToRootCause?: () => void
}

export const BehaviorTimeline: React.FC<BehaviorTimelineProps> = ({
  onSelectEvent,
  onNavigateToRootCause,
}) => {
  const {
    summary,
    activeCategory,
    activeSeverity,
    selectedEvent,
    setActiveCategory,
    setActiveSeverity,
    setSelectedEvent,
  } = useComparisonStore()

  const categories: Array<{ id: DiffCategory | 'all'; label: string; icon?: React.ReactNode }> = [
    { id: 'all', label: 'All Events' },
    { id: 'network', label: 'Network', icon: <Globe size={13} /> },
    { id: 'dom', label: 'DOM', icon: <Layers size={13} /> },
    { id: 'console', label: 'Console', icon: <Terminal size={13} /> },
    { id: 'storage', label: 'Storage', icon: <Database size={13} /> },
  ]

  const severities: Array<SeverityLevel | 'all'> = ['all', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

  const filteredTimeline = summary.timeline.filter((evt) => {
    if (activeCategory !== 'all' && evt.category !== activeCategory) return false
    if (activeSeverity !== 'all' && evt.severity !== activeSeverity) return false
    return true
  })

  const handleCardClick = (evt: TimelineEvent) => {
    setSelectedEvent(evt)
    if (onSelectEvent) onSelectEvent(evt)
  }

  const getCategoryIcon = (cat: DiffCategory) => {
    switch (cat) {
      case 'network': return <Globe size={14} />
      case 'dom': return <Layers size={14} />
      case 'console': return <Terminal size={14} />
      case 'storage': return <Database size={14} />
      default: return <Clock size={14} />
    }
  }

  return (
    <div className="sd-timeline-viewer animate-fade-in">
      <SectionHeader
        title="Behavior Divergence Timeline"
        subtitle="Chronological sequence of runtime events comparing Commit A vs Commit B, pinpointing the exact moment behavior diverged."
        icon={<GitCompare size={20} />}
        actions={
          onNavigateToRootCause && (
            <Button variant="cyan" size="sm" onClick={onNavigateToRootCause}>
              Trace to Root Cause →
            </Button>
          )
        }
      />

      {/* Filter Toolbar */}
      <div className="sd-timeline__filters">
        <div className="sd-timeline__filter-group">
          <span className="sd-timeline__filter-label">
            <Filter size={13} /> Category:
          </span>
          <div className="sd-timeline__filter-pills">
            {categories.map((cat) => (
              <button
                key={cat.id}
                className={`sd-filter-pill ${activeCategory === cat.id ? 'is-active' : ''}`}
                onClick={() => setActiveCategory(cat.id)}
              >
                {cat.icon}
                <span>{cat.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="sd-timeline__filter-group">
          <span className="sd-timeline__filter-label">Severity:</span>
          <div className="sd-timeline__filter-pills">
            {severities.map((sev) => (
              <button
                key={sev}
                className={`sd-filter-pill ${activeSeverity === sev ? 'is-active' : ''} ${sev !== 'all' ? `is-${sev.toLowerCase()}` : ''}`}
                onClick={() => setActiveSeverity(sev)}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline Stream + Details Split */}
      <div className="sd-timeline__content-split">
        {/* Stream List */}
        <div className="sd-timeline__stream">
          {filteredTimeline.map((evt) => {
            const isSelected = selectedEvent?.id === evt.id
            const isDivergence = evt.isFirstDivergence

            return (
              <div
                key={evt.id}
                className={`sd-timeline-node ${isSelected ? 'is-selected' : ''} ${isDivergence ? 'is-divergence' : ''}`}
                onClick={() => handleCardClick(evt)}
              >
                {/* Node Beacon */}
                <div className="sd-timeline-node__indicator">
                  <div className={`sd-timeline-node__dot is-${evt.severity.toLowerCase()}`}>
                    {isDivergence ? <AlertOctagon size={14} /> : getCategoryIcon(evt.category)}
                  </div>
                  <div className="sd-timeline-node__line" />
                </div>

                {/* Node Card */}
                <Card
                  variant={isDivergence ? 'glass' : 'default'}
                  className={`sd-timeline-node__card ${isDivergence ? 'glow-critical' : ''}`}
                >
                  <CardHeader>
                    <div className="sd-timeline-node__header-row">
                      <div className="sd-timeline-node__meta">
                        <span className="sd-timeline-node__step">Step #{evt.stepIndex}</span>
                        <code className="sd-timeline-node__time">{evt.timestamp}</code>
                        <span className="sd-timeline-node__route">{evt.route}</span>
                      </div>
                      <div className="sd-timeline-node__badges">
                        {isDivergence && (
                          <Badge severity="CRITICAL" size="sm" dot glow>
                            FIRST DIVERGENCE
                          </Badge>
                        )}
                        <Badge severity={evt.severity} size="sm">
                          {evt.severity}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <h4 className="sd-timeline-node__title">{evt.title}</h4>
                    <p className="sd-timeline-node__desc">{evt.description}</p>
                    <div className="sd-timeline-node__footer">
                      <span className="sd-timeline-node__ev-count">
                        {evt.evidenceCount} evidence artifacts indexed
                      </span>
                      <span className="sd-timeline-node__view-btn">
                        View Details <ArrowRight size={12} />
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )
          })}
        </div>

        {/* Selected Event Deep Dive Panel */}
        {selectedEvent && (
          <div className="sd-timeline__detail-pane">
            <Card variant="glass" className="sd-timeline__inspector-card">
              <CardHeader>
                <CardTitle>
                  <AlertOctagon size={16} className="text-cyan" /> Event Inspector
                </CardTitle>
                <Badge severity={selectedEvent.severity} size="sm">
                  {selectedEvent.severity}
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="sd-timeline-inspector__content">
                  <h4 className="sd-timeline-inspector__title">{selectedEvent.title}</h4>
                  <p className="sd-timeline-inspector__desc">{selectedEvent.description}</p>

                  <div className="sd-timeline-inspector__meta-table">
                    <div className="sd-inspector-row">
                      <span className="label">Step Index</span>
                      <span className="val">#{selectedEvent.stepIndex}</span>
                    </div>
                    <div className="sd-inspector-row">
                      <span className="label">Timestamp</span>
                      <span className="val font-mono">{selectedEvent.timestamp}</span>
                    </div>
                    <div className="sd-inspector-row">
                      <span className="label">Category</span>
                      <span className="val uppercase font-mono">{selectedEvent.category}</span>
                    </div>
                    <div className="sd-inspector-row">
                      <span className="label">Route Path</span>
                      <span className="val font-mono text-cyan">{selectedEvent.route}</span>
                    </div>
                  </div>

                  {selectedEvent.details && (
                    <div className="sd-timeline-inspector__json-section">
                      <span className="sd-inspector-label">Runtime Comparison Evidence:</span>
                      <pre className="sd-inspector-pre">
                        {JSON.stringify(selectedEvent.details, null, 2)}
                      </pre>
                    </div>
                  )}

                  {onNavigateToRootCause && (
                    <Button
                      variant="cyan"
                      size="sm"
                      className="sd-timeline-inspector__action-btn"
                      onClick={onNavigateToRootCause}
                    >
                      Correlate with Code Cause →
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
