import React from 'react'
import {
  GitBranch,
  GitCommit,
  ArrowRight,
  Clock,
  User,
  ExternalLink,
  CheckCircle,
} from 'lucide-react'
import { useRepositoryStore } from '../../store'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './RepositoryExplorer.css'

export interface RepositoryExplorerProps {
  onTriggerRuntime?: () => void
}

export const RepositoryExplorer: React.FC<RepositoryExplorerProps> = ({ onTriggerRuntime }) => {
  const { repository, setBaseCommit, setHeadCommit } = useRepositoryStore()
  const { baseCommit, headCommit, recentCommits } = repository

  return (
    <div className="sd-repo-explorer animate-fade-in">
      <SectionHeader
        title="Git Repository & Commit Comparator"
        subtitle="Select baseline and head commits to discover and isolate behavioral runtime regressions."
        icon={<GitBranch size={20} />}
        actions={
          <Button variant="cyan" size="sm" onClick={onTriggerRuntime}>
            Collect Traces for Target
          </Button>
        }
      />

      {/* Target Comparison Bar */}
      <div className="sd-repo-explorer__comparison-grid">
        {/* Base Commit A */}
        <Card variant="glass" className="sd-repo-explorer__commit-card">
          <CardHeader>
            <div className="sd-repo-explorer__commit-header">
              <Badge severity="LOW" size="sm">Baseline (Commit A)</Badge>
              <code className="sd-repo-explorer__sha">{baseCommit.shortSha}</code>
            </div>
          </CardHeader>
          <CardContent>
            <h4 className="sd-repo-explorer__commit-msg">{baseCommit.message}</h4>
            <div className="sd-repo-explorer__meta-row">
              <span className="sd-repo-explorer__meta-item">
                <User size={13} /> {baseCommit.author}
              </span>
              <span className="sd-repo-explorer__meta-item">
                <Clock size={13} /> {baseCommit.timestamp}
              </span>
            </div>
            <div className="sd-repo-explorer__stats">
              <span className="stat-changed">{baseCommit.filesChanged || 3} files changed</span>
              <span className="stat-add">+{baseCommit.insertions || 48}</span>
              <span className="stat-del">-{baseCommit.deletions || 12}</span>
            </div>
          </CardContent>
        </Card>

        {/* Arrow Divider */}
        <div className="sd-repo-explorer__divider">
          <ArrowRight size={24} className="sd-repo-explorer__divider-icon" />
          <span className="sd-repo-explorer__divider-text">Runtime Diff</span>
        </div>

        {/* Head Commit B */}
        <Card variant="glass" className="sd-repo-explorer__commit-card is-head">
          <CardHeader>
            <div className="sd-repo-explorer__commit-header">
              <Badge severity="CRITICAL" size="sm" dot glow>Under Review (Commit B)</Badge>
              <code className="sd-repo-explorer__sha">{headCommit.shortSha}</code>
            </div>
          </CardHeader>
          <CardContent>
            <h4 className="sd-repo-explorer__commit-msg">{headCommit.message}</h4>
            <div className="sd-repo-explorer__meta-row">
              <span className="sd-repo-explorer__meta-item">
                <User size={13} /> {headCommit.author}
              </span>
              <span className="sd-repo-explorer__meta-item">
                <Clock size={13} /> {headCommit.timestamp}
              </span>
            </div>
            <div className="sd-repo-explorer__stats">
              <span className="stat-changed">{headCommit.filesChanged || 1} files changed</span>
              <span className="stat-add">+{headCommit.insertions || 2}</span>
              <span className="stat-del">-{headCommit.deletions || 6}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Commit History Selection Table */}
      <Card className="sd-repo-explorer__history-card">
        <CardHeader>
          <CardTitle>
            <GitCommit size={16} /> Recent Commit History
          </CardTitle>
          <div className="sd-repo-explorer__repo-link">
            <span>{repository.name}</span>
            <ExternalLink size={13} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="sd-repo-explorer__table-wrapper">
            <table className="sd-repo-explorer__table">
              <thead>
                <tr>
                  <th>Commit SHA</th>
                  <th>Message</th>
                  <th>Author</th>
                  <th>Timestamp</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentCommits.map((c) => {
                  const isBase = c.sha === baseCommit.sha
                  const isHead = c.sha === headCommit.sha

                  return (
                    <tr key={c.sha} className={isHead ? 'is-selected-head' : isBase ? 'is-selected-base' : ''}>
                      <td>
                        <div className="sd-repo-explorer__table-sha">
                          <code>{c.shortSha}</code>
                          {isBase && <Badge severity="LOW" size="sm">Base A</Badge>}
                          {isHead && <Badge severity="CRITICAL" size="sm">Head B</Badge>}
                        </div>
                      </td>
                      <td className="sd-repo-explorer__table-msg">{c.message}</td>
                      <td>{c.author}</td>
                      <td className="text-muted">{c.timestamp}</td>
                      <td>
                        <div className="sd-repo-explorer__table-actions">
                          <Button
                            variant={isBase ? 'secondary' : 'outline'}
                            size="sm"
                            disabled={isBase}
                            onClick={() => setBaseCommit(c)}
                          >
                            {isBase ? <CheckCircle size={12} /> : 'Set Base A'}
                          </Button>
                          <Button
                            variant={isHead ? 'secondary' : 'outline'}
                            size="sm"
                            disabled={isHead}
                            onClick={() => setHeadCommit(c)}
                          >
                            {isHead ? <CheckCircle size={12} /> : 'Set Head B'}
                          </Button>
                        </div>
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
