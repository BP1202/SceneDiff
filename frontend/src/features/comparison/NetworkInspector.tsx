import React, { useState } from 'react'
import {
  Globe,
  AlertTriangle,
  ArrowRight,
  Filter,
} from 'lucide-react'
import { useComparisonStore } from '../../store'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './NetworkInspector.css'

export const NetworkInspector: React.FC = () => {
  const { summary } = useComparisonStore()
  const [onlyRegressions, setOnlyRegressions] = useState(false)

  const filtered = onlyRegressions
    ? summary.networkDiffs.filter((n) => n.isRegression)
    : summary.networkDiffs

  return (
    <div className="sd-network-inspector animate-fade-in">
      <SectionHeader
        title="Network & API Behavior Inspector"
        subtitle="Identifies HTTP status code divergences, dropped network transactions, and payload parsing crashes."
        icon={<Globe size={20} />}
        actions={
          <button
            className={`sd-filter-toggle ${onlyRegressions ? 'is-active' : ''}`}
            onClick={() => setOnlyRegressions((prev) => !prev)}
          >
            <Filter size={13} />
            <span>Show Regressions Only</span>
          </button>
        }
      />

      {/* Network Traffic Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Globe size={16} /> HTTP Network Invocations ({filtered.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="sd-network-table-wrapper">
            <table className="sd-network-table">
              <thead>
                <tr>
                  <th>Method & Endpoint</th>
                  <th>Commit A (Base)</th>
                  <th>Commit B (Head)</th>
                  <th>Latency Comparison</th>
                  <th>Status Divergence</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const isFail = item.headStatus === 500 || item.headStatus === 0
                  return (
                    <tr key={item.id} className={item.isRegression ? 'is-regression-row' : ''}>
                      <td>
                        <div className="sd-network-endpoint">
                          <span className={`sd-method-badge is-${item.method.toLowerCase()}`}>
                            {item.method}
                          </span>
                          <code className="sd-network-url">{item.url}</code>
                        </div>
                        {item.errorDetail && (
                          <div className="sd-network-error-detail">
                            <AlertTriangle size={12} />
                            <span>{item.errorDetail}</span>
                          </div>
                        )}
                      </td>
                      <td>
                        <span className="sd-status-pill is-200">
                          {item.baseStatus || 'N/A'}
                        </span>
                      </td>
                      <td>
                        <span className={`sd-status-pill ${isFail ? 'is-500' : 'is-200'}`}>
                          {item.headStatus === 0 ? 'DROPPED (0)' : item.headStatus}
                        </span>
                      </td>
                      <td>
                        <div className="sd-latency-bar-cell">
                          <div className="sd-latency-text">
                            <span>{item.baseLatencyMs}ms</span>
                            <ArrowRight size={11} />
                            <span className={item.headLatencyMs && item.headLatencyMs > 400 ? 'text-critical' : ''}>
                              {item.headLatencyMs}ms
                            </span>
                          </div>
                          <div className="sd-latency-meter">
                            <div
                              className="sd-latency-fill is-base"
                              style={{ width: `${Math.min(100, ((item.baseLatencyMs || 0) / 700) * 100)}%` }}
                            />
                            <div
                              className="sd-latency-fill is-head"
                              style={{ width: `${Math.min(100, ((item.headLatencyMs || 0) / 700) * 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td>
                        {item.isRegression ? (
                          <Badge severity="CRITICAL" size="sm" dot glow>
                            REGRESSION
                          </Badge>
                        ) : (
                          <Badge severity="SUCCESS" size="sm">
                            MATCH
                          </Badge>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
