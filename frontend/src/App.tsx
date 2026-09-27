import React, { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  GitCompare,
  Layers,
  Globe,
  Terminal,
  Gauge,
  BrainCircuit,
  Share2,
} from 'lucide-react'
import { WorkspaceShell } from './components/layouts'
import { Tabs } from './components/ui/Tabs'
import {
  useRepositoryStore,
  useRuntimeStore,
  useComparisonStore,
  useRootCauseStore,
  useRepairStore,
  useUiStore,
} from './store'
import { DashboardOverview } from './features/dashboard/DashboardOverview'
import { RuntimeCollector } from './features/runtime/RuntimeCollector'
import { BehaviorTimeline } from './features/comparison/BehaviorTimeline'
import { DOMDiffViewer } from './features/comparison/DOMDiffViewer'
import { NetworkInspector } from './features/comparison/NetworkInspector'
import { ConsoleStorageViewer } from './features/comparison/ConsoleStorageViewer'
import { PerformanceDashboard } from './features/comparison/PerformanceDashboard'
import { RootCauseExplorer } from './features/rootcause/RootCauseExplorer'
import { EvidenceGraph } from './features/rootcause/EvidenceGraph'
import { RepairStudio } from './features/repair/RepairStudio'
import { ExportCenter } from './features/reports/ExportCenter'
import './theme/globals.css'
import './App.css'

const queryClient = new QueryClient()

export const AppContent: React.FC = () => {
  const { currentView, setCurrentView } = useUiStore()
  const { repository, setTarget } = useRepositoryStore()
  const { isRunning, startExecution, finishExecution } = useRuntimeStore()
  const { summary } = useComparisonStore()
  const { report } = useRootCauseStore()
  const { repair } = useRepairStore()

  // Sub-tabs for Comparison view
  const [comparisonSubTab, setComparisonSubTab] = useState<'timeline' | 'dom' | 'network' | 'console' | 'perf'>('timeline')
  // Sub-tabs for Root Cause view
  const [rootCauseSubTab, setRootCauseSubTab] = useState<'analysis' | 'graph'>('analysis')

  const handleRunRuntime = () => {
    startExecution()
    setTimeout(() => {
      finishExecution()
    }, 1200)
  }

  const comparisonTabs = [
    { id: 'timeline', label: 'Divergence Timeline', icon: <GitCompare size={14} />, severity: 'CRITICAL' as const, count: summary.timeline.length },
    { id: 'dom', label: 'DOM Tree Diff', icon: <Layers size={14} />, count: summary.domDiffs.length },
    { id: 'network', label: 'Network Inspector', icon: <Globe size={14} />, count: summary.networkDiffs.length },
    { id: 'console', label: 'Console & Storage', icon: <Terminal size={14} />, count: summary.consoleDiffs.length + summary.storageDiffs.length },
    { id: 'perf', label: 'Performance Vitals', icon: <Gauge size={14} /> },
  ]

  const rootCauseTabs = [
    { id: 'analysis', label: 'Root Cause Synthesis', icon: <BrainCircuit size={14} /> },
    { id: 'graph', label: 'Interactive Causal Graph', icon: <Share2 size={14} /> },
  ]

  return (
    <WorkspaceShell
      currentView={currentView}
      onSelectView={setCurrentView}
      repositoryName={repository.name}
      branchName={repository.defaultBranch}
      baseCommit={repository.baseCommit.sha}
      headCommit={repository.headCommit.sha}
      isRunningRuntime={isRunning}
      onRunRuntime={handleRunRuntime}
      onUpdateRepoTarget={(name, base, head) => setTarget(name, base, head)}
      regressionsCount={summary.severityCounts.CRITICAL + summary.severityCounts.HIGH}
      pendingRepairsCount={repair.status === 'proposed' ? 1 : 0}
      culpritFile={report.primaryCandidate.file}
      culpritFunction={report.primaryCandidate.functionName}
      confidenceScore={report.rootCauseConfidence}
      riskLevel={repair.risk.level}
    >
      {/* View 1: Dashboard Overview */}
      {currentView === 'dashboard' && (
        <DashboardOverview
          onNavigate={setCurrentView}
          onRunRuntime={handleRunRuntime}
          isRunningRuntime={isRunning}
        />
      )}

      {/* View 2: Runtime Collector */}
      {currentView === 'runtime' && (
        <RuntimeCollector onNavigateToComparison={() => setCurrentView('comparison')} />
      )}

      {/* View 3: Behavior Diff & Comparison Sub-modules */}
      {currentView === 'comparison' && (
        <div className="sd-comparison-view animate-fade-in">
          <Tabs
            tabs={comparisonTabs}
            activeTab={comparisonSubTab}
            onChange={(tab) => setComparisonSubTab(tab as typeof comparisonSubTab)}
            className="sd-comparison-subtabs"
          />

          <div className="sd-comparison-subcontent">
            {comparisonSubTab === 'timeline' && (
              <BehaviorTimeline onNavigateToRootCause={() => setCurrentView('rootcause')} />
            )}
            {comparisonSubTab === 'dom' && <DOMDiffViewer />}
            {comparisonSubTab === 'network' && <NetworkInspector />}
            {comparisonSubTab === 'console' && <ConsoleStorageViewer />}
            {comparisonSubTab === 'perf' && <PerformanceDashboard />}
          </div>
        </div>
      )}

      {/* View 4: Root Cause Explorer & Evidence Graph */}
      {currentView === 'rootcause' && (
        <div className="sd-rootcause-view animate-fade-in">
          <Tabs
            tabs={rootCauseTabs}
            activeTab={rootCauseSubTab}
            onChange={(tab) => setRootCauseSubTab(tab as typeof rootCauseSubTab)}
            className="sd-rootcause-subtabs"
          />

          <div className="sd-rootcause-subcontent">
            {rootCauseSubTab === 'analysis' ? (
              <RootCauseExplorer
                onNavigateToRepair={() => setCurrentView('repair')}
                onToggleGraphView={() => setRootCauseSubTab('graph')}
              />
            ) : (
              <EvidenceGraph />
            )}
          </div>
        </div>
      )}

      {/* View 5: Repair Studio */}
      {currentView === 'repair' && (
        <RepairStudio onNavigateToExport={() => setCurrentView('export')} />
      )}

      {/* View 6: Export Center */}
      {currentView === 'export' && <ExportCenter />}
    </WorkspaceShell>
  )
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App
