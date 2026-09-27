import React, { useState, useEffect } from 'react'
import { Sidebar, NavView } from './Sidebar'
import { TopNavbar } from './TopNavbar'
import { AiInspectorDrawer } from './AiInspectorDrawer'
import { CommandPalette } from './CommandPalette'
import { RepoSelectorModal } from './RepoSelectorModal'
import './WorkspaceShell.css'

export interface WorkspaceShellProps {
  currentView: NavView
  onSelectView: (view: NavView) => void
  children: React.ReactNode
  repositoryName?: string
  branchName?: string
  baseCommit?: string
  headCommit?: string
  isRunningRuntime?: boolean
  onRunRuntime?: () => void
  onUpdateRepoTarget?: (repo: string, base: string, head: string) => void
  regressionsCount?: number
  pendingRepairsCount?: number
  culpritFile?: string
  culpritFunction?: string
  confidenceScore?: number
  riskLevel?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'INFO'
}

export const WorkspaceShell: React.FC<WorkspaceShellProps> = ({
  currentView,
  onSelectView,
  children,
  repositoryName = 'BP1202/SceneDiff',
  branchName = 'main',
  baseCommit = 'f4a180d297a1b',
  headCommit = 'e93b11c841b9c',
  isRunningRuntime = false,
  onRunRuntime = () => {},
  onUpdateRepoTarget = () => {},
  regressionsCount = 3,
  pendingRepairsCount = 1,
  culpritFile = 'app/auth/login.py',
  culpritFunction = 'validate_token',
  confidenceScore = 94,
  riskLevel = 'HIGH',
}) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(true)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [isRepoModalOpen, setIsRepoModalOpen] = useState(false)

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K: Command Palette
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setIsCommandPaletteOpen((prev) => !prev)
      }
      // Cmd/Ctrl + R: Run Runtime
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'r' && !e.shiftKey) {
        // Prevent default only if inside active workspace
        if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
        e.preventDefault()
        onRunRuntime()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onRunRuntime])

  return (
    <div className="sd-workspace-shell">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onSelectView={onSelectView}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        regressionsCount={regressionsCount}
        pendingRepairsCount={pendingRepairsCount}
      />

      {/* Main Flow (TopNav + Content + Right AI Inspector) */}
      <div className="sd-workspace-shell__main-column">
        <TopNavbar
          repositoryName={repositoryName}
          branchName={branchName}
          baseCommit={baseCommit}
          headCommit={headCommit}
          isRunningRuntime={isRunningRuntime}
          onRunRuntime={onRunRuntime}
          onOpenRepoSelector={() => setIsRepoModalOpen(true)}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          isAiDrawerOpen={isAiDrawerOpen}
          onToggleAiDrawer={() => setIsAiDrawerOpen((prev) => !prev)}
        />

        <div className="sd-workspace-shell__content-area">
          {/* Main Visualizer Container */}
          <main className="sd-workspace-shell__center">
            {children}
          </main>

          {/* Right AI Inspector Drawer */}
          <AiInspectorDrawer
            isOpen={isAiDrawerOpen}
            onClose={() => setIsAiDrawerOpen(false)}
            onNavigateToRepair={() => onSelectView('repair')}
            onNavigateToRootCause={() => onSelectView('rootcause')}
            culpritFile={culpritFile}
            culpritFunction={culpritFunction}
            confidenceScore={confidenceScore}
            riskLevel={riskLevel}
          />
        </div>
      </div>

      {/* Modals */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectView={onSelectView}
        onRunRuntime={onRunRuntime}
      />

      <RepoSelectorModal
        isOpen={isRepoModalOpen}
        onClose={() => setIsRepoModalOpen(false)}
        currentRepo={repositoryName}
        currentBaseCommit={baseCommit}
        currentHeadCommit={headCommit}
        onSave={onUpdateRepoTarget}
      />
    </div>
  )
}
