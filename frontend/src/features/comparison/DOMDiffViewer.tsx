import React, { useState } from 'react'
import {
  Layers,
  Search,
  CheckCircle,
  AlertCircle,
  Eye,
  Code2,
} from 'lucide-react'
import { useComparisonStore } from '../../store'
import { DOMDiffItem } from '../../types'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './DOMDiffViewer.css'

export const DOMDiffViewer: React.FC = () => {
  const { summary } = useComparisonStore()
  const [search, setSearch] = useState('')
  const [selectedDiff, setSelectedDiff] = useState<DOMDiffItem | null>(summary.domDiffs[0] || null)

  const filtered = summary.domDiffs.filter((d) =>
    d.selector.toLowerCase().includes(search.toLowerCase()) ||
    d.xpath.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="sd-dom-diff animate-fade-in">
      <SectionHeader
        title="DOM Tree Mutation Analyzer"
        subtitle="Side-by-side inspection of interactive element additions, removals, attribute alterations, and state traps between Commit A and Commit B."
        icon={<Layers size={20} />}
      />

      {/* Visual State Comparison Simulation */}
      <div className="sd-dom-diff__viewport-grid">
        <Card variant="glass" className="sd-dom-viewport-card">
          <CardHeader>
            <CardTitle>
              <Eye size={15} /> Base Commit A (Baseline DOM)
            </CardTitle>
            <Badge severity="SUCCESS" size="sm">Healthy</Badge>
          </CardHeader>
          <CardContent className="sd-dom-viewport__frame">
            <div className="mock-browser-window">
              <div className="mock-browser-bar">http://localhost:5173/login</div>
              <div className="mock-browser-content">
                <div className="mock-form">
                  <div className="mock-input">user@company.ibm.com</div>
                  <div className="mock-input">••••••••••••</div>
                  <div className="mock-button mock-button--success">
                    Sign In (Ready)
                  </div>
                  <div className="mock-tag is-pass">
                    <CheckCircle size={12} /> Authenticated successfully → redirected
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card variant="glass" className="sd-dom-viewport-card is-diverged">
          <CardHeader>
            <CardTitle>
              <Eye size={15} /> Head Commit B (Regressed DOM)
            </CardTitle>
            <Badge severity="CRITICAL" size="sm" dot glow>Regression Detected</Badge>
          </CardHeader>
          <CardContent className="sd-dom-viewport__frame">
            <div className="mock-browser-window">
              <div className="mock-browser-bar">http://localhost:5173/login</div>
              <div className="mock-browser-content">
                <div className="mock-form">
                  <div className="mock-input">user@company.ibm.com</div>
                  <div className="mock-input">••••••••••••</div>
                  <div className="mock-button mock-button--loading">
                    Signing In... (Trapped in loading)
                  </div>
                  <div className="mock-banner is-fail">
                    <AlertCircle size={13} /> Unexpected Server Error (500)
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* DOM Mutations Table */}
      <Card className="sd-dom-diff__table-card">
        <CardHeader>
          <CardTitle>
            <Code2 size={16} /> DOM Mutation Index ({summary.domDiffs.length} mutations)
          </CardTitle>
          <div className="sd-dom-diff__search-box">
            <Search size={14} />
            <input
              type="text"
              placeholder="Filter by selector or xpath..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="sd-dom-diff__search-input"
            />
          </div>
        </CardHeader>
        <CardContent>
          <div className="sd-dom-diff__table-wrapper">
            <table className="sd-dom-diff__table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>DOM Selector</th>
                  <th>Mutation Type</th>
                  <th>Baseline Value (Commit A)</th>
                  <th>Regressed Value (Commit B)</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const isSelected = selectedDiff?.id === item.id
                  return (
                    <tr
                      key={item.id}
                      className={isSelected ? 'is-selected' : ''}
                      onClick={() => setSelectedDiff(item)}
                    >
                      <td>
                        <Badge severity={item.severity} size="sm">
                          {item.severity}
                        </Badge>
                      </td>
                      <td>
                        <div className="sd-dom-selector-cell">
                          <code>{item.selector}</code>
                          <span className="sd-xpath-hint">{item.xpath}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`sd-mutation-type is-${item.changeType}`}>
                          {item.changeType.replace('_', ' ')}
                        </span>
                      </td>
                      <td>
                        <code className="sd-val-base">{item.baseValue || '(none)'}</code>
                      </td>
                      <td>
                        <code className="sd-val-head">{item.headValue || '(none)'}</code>
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
