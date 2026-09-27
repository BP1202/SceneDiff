import React from 'react'
import {
  Share2,
  GitCommit,
  FileCode,
  Globe,
  Terminal,
  Layers,
  Database,
  ArrowRight,
  Info,
} from 'lucide-react'
import { useRootCauseStore } from '../../store'
import { EvidenceNode } from '../../types'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { SectionHeader } from '../../components/ui/SectionHeader'
import './EvidenceGraph.css'

export const EvidenceGraph: React.FC = () => {
  const { report, selectedNode, setSelectedNode } = useRootCauseStore()
  const { evidenceNodes, evidenceEdges } = report

  const getNodeIcon = (cat: EvidenceNode['category']) => {
    switch (cat) {
      case 'commit': return <GitCommit size={16} />
      case 'code': return <FileCode size={16} />
      case 'network': return <Globe size={16} />
      case 'console': return <Terminal size={16} />
      case 'dom': return <Layers size={16} />
      case 'storage': return <Database size={16} />
    }
  }

  return (
    <div className="sd-evidence-graph animate-fade-in">
      <SectionHeader
        title="Interactive Causal Evidence Graph"
        subtitle="Directed acyclic graph illustrating how code modification in Commit B propagated into network failure, browser console exception, and UI lockup."
        icon={<Share2 size={20} />}
      />

      <div className="sd-graph-split">
        {/* Visual Graph Canvas Container */}
        <Card variant="glass" className="sd-graph-canvas-card">
          <CardHeader>
            <CardTitle>
              <Share2 size={15} className="text-cyan" /> Causal Propagation Flow
            </CardTitle>
            <span className="sd-graph-hint">Click any node to inspect evidence artifact</span>
          </CardHeader>
          <CardContent className="sd-graph-canvas">
            {/* Visual Node Diagram */}
            <div className="sd-graph-nodes-layout">
              {/* Layer 1: Git Commit */}
              <div className="sd-graph-layer">
                <span className="sd-graph-layer-title">Git Code Change</span>
                {evidenceNodes
                  .filter((n) => n.category === 'commit' || n.category === 'code')
                  .map((node) => {
                    const isSelected = selectedNode?.id === node.id
                    return (
                      <div
                        key={node.id}
                        className={`sd-graph-node is-${node.category} ${isSelected ? 'is-selected' : ''}`}
                        onClick={() => setSelectedNode(node)}
                      >
                        <div className="sd-graph-node__icon">{getNodeIcon(node.category)}</div>
                        <div className="sd-graph-node__body">
                          <span className="sd-graph-node__label">{node.label}</span>
                          <span className="sd-graph-node__desc">{node.description}</span>
                        </div>
                        {node.severity && (
                          <Badge severity={node.severity} size="sm">
                            {node.severity}
                          </Badge>
                        )}
                      </div>
                    )
                  })}
              </div>

              {/* Edge Arrows */}
              <div className="sd-graph-arrows-column">
                <div className="sd-graph-arrow-item">
                  <ArrowRight size={20} className="text-cyan" />
                  <span className="sd-arrow-label">triggers</span>
                </div>
              </div>

              {/* Layer 2: Runtime Network & Console */}
              <div className="sd-graph-layer">
                <span className="sd-graph-layer-title">Runtime Failure</span>
                {evidenceNodes
                  .filter((n) => n.category === 'network' || n.category === 'console')
                  .map((node) => {
                    const isSelected = selectedNode?.id === node.id
                    return (
                      <div
                        key={node.id}
                        className={`sd-graph-node is-${node.category} ${isSelected ? 'is-selected' : ''}`}
                        onClick={() => setSelectedNode(node)}
                      >
                        <div className="sd-graph-node__icon">{getNodeIcon(node.category)}</div>
                        <div className="sd-graph-node__body">
                          <span className="sd-graph-node__label">{node.label}</span>
                          <span className="sd-graph-node__desc">{node.description}</span>
                        </div>
                        {node.severity && (
                          <Badge severity={node.severity} size="sm">
                            {node.severity}
                          </Badge>
                        )}
                      </div>
                    )
                  })}
              </div>

              {/* Edge Arrows */}
              <div className="sd-graph-arrows-column">
                <div className="sd-graph-arrow-item">
                  <ArrowRight size={20} className="text-cyan" />
                  <span className="sd-arrow-label">results in</span>
                </div>
              </div>

              {/* Layer 3: DOM & Storage */}
              <div className="sd-graph-layer">
                <span className="sd-graph-layer-title">User Impact (Symptom)</span>
                {evidenceNodes
                  .filter((n) => n.category === 'dom' || n.category === 'storage')
                  .map((node) => {
                    const isSelected = selectedNode?.id === node.id
                    return (
                      <div
                        key={node.id}
                        className={`sd-graph-node is-${node.category} ${isSelected ? 'is-selected' : ''}`}
                        onClick={() => setSelectedNode(node)}
                      >
                        <div className="sd-graph-node__icon">{getNodeIcon(node.category)}</div>
                        <div className="sd-graph-node__body">
                          <span className="sd-graph-node__label">{node.label}</span>
                          <span className="sd-graph-node__desc">{node.description}</span>
                        </div>
                        {node.severity && (
                          <Badge severity={node.severity} size="sm">
                            {node.severity}
                          </Badge>
                        )}
                      </div>
                    )
                  })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Selected Evidence Node Details */}
        {selectedNode && (
          <Card className="sd-graph-detail-card">
            <CardHeader>
              <CardTitle>
                <Info size={16} /> Evidence Artifact Inspector
              </CardTitle>
              {selectedNode.severity && (
                <Badge severity={selectedNode.severity} size="sm">
                  {selectedNode.severity}
                </Badge>
              )}
            </CardHeader>
            <CardContent>
              <div className="sd-node-detail-pane">
                <div className="sd-node-detail-header">
                  <div className="sd-node-detail-icon">{getNodeIcon(selectedNode.category)}</div>
                  <div>
                    <h4 className="sd-node-detail-title">{selectedNode.label}</h4>
                    <span className="sd-node-detail-cat font-mono uppercase">{selectedNode.category}</span>
                  </div>
                </div>

                <div className="sd-node-detail-desc">
                  <span className="label">Observed Evidence:</span>
                  <p>{selectedNode.description}</p>
                </div>

                <div className="sd-node-connections">
                  <span className="label">Connected Causal Relationships:</span>
                  <div className="sd-connections-list">
                    {evidenceEdges
                      .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                      .map((edge) => (
                        <div key={edge.id} className="sd-edge-item">
                          <code>{edge.source}</code>
                          <span className="sd-edge-rel">--[{edge.relation}]--&gt;</span>
                          <code>{edge.target}</code>
                          <span className="sd-edge-weight">Weight: {edge.weight}</span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
