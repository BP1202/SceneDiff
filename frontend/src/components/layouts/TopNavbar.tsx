import React from 'react'
import {
  GitBranch,
  Play,
  Search,
  PanelRightClose,
  PanelRightOpen,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react'
import { Button } from '../ui/Button'
import './TopNavbar.css'

export interface TopNavbarProps {
  repositoryName: string
  branchName: string
  baseCommit: string
  headCommit: string
  isRunningRuntime: boolean
  onRunRuntime: () => void
  onOpenRepoSelector: () => void
  onOpenCommandPalette: () => void
  isAiDrawerOpen: boolean
  onToggleAiDrawer: () => void
  isBackendHealthy?: boolean
}

export const TopNavbar: React.FC<TopNavbarProps> = ({
  repositoryName,
  branchName,
  baseCommit,
  headCommit,
  isRunningRuntime,
  onRunRuntime,
  onOpenRepoSelector,
  onOpenCommandPalette,
  isAiDrawerOpen,
  onToggleAiDrawer,
  isBackendHealthy = true,
}) => {
  return (
    <header className="sd-top-navbar">
      {/* Left: Repo and Branch Picker */}
      <div className="sd-top-navbar__left">
        <button
          className="sd-top-navbar__repo-badge"
          onClick={onOpenRepoSelector}
          title="Change Repository"
        >
          <GitBranch size={15} className="sd-top-navbar__repo-icon" />
          <span className="sd-top-navbar__repo-name">{repositoryName}</span>
          <span className="sd-top-navbar__branch-tag">{branchName}</span>
        </button>

        {/* Dual Commit Pills */}
        <div className="sd-top-navbar__commits">
          <span className="sd-top-navbar__commit-pill" title="Base Commit (Sprint 4 Baseline)">
            <span className="sd-top-navbar__commit-prefix">A:</span>
            <code>{baseCommit.slice(0, 7)}</code>
          </span>
          <ArrowRight size={14} className="sd-top-navbar__commit-arrow" />
          <span className="sd-top-navbar__commit-pill is-head" title="Head Commit (Under Review)">
            <span className="sd-top-navbar__commit-prefix">B:</span>
            <code>{headCommit.slice(0, 7)}</code>
          </span>
        </div>
      </div>

      {/* Center: Command Palette Trigger */}
      <div className="sd-top-navbar__center">
        <button
          className="sd-top-navbar__search-trigger"
          onClick={onOpenCommandPalette}
          title="Open Command Palette (Ctrl+K)"
        >
          <Search size={14} />
          <span>Search divergences, culprit files, patches...</span>
          <kbd className="sd-top-navbar__kbd">⌘K</kbd>
        </button>
      </div>

      {/* Right: Actions & Status */}
      <div className="sd-top-navbar__right">
        {/* Backend Health Status */}
        <div className={`sd-top-navbar__health ${isBackendHealthy ? 'is-healthy' : 'is-unhealthy'}`} title={isBackendHealthy ? 'Backend API Connected' : 'Backend Disconnected'}>
          {isBackendHealthy ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
          <span className="sd-top-navbar__health-label">API 2.0</span>
        </div>

        {/* Primary CTA: Run Runtime */}
        <Button
          variant="cyan"
          size="sm"
          icon={<Play size={14} />}
          isLoading={isRunningRuntime}
          onClick={onRunRuntime}
          title="Launch Playwright Runtime Trace Collector (Ctrl+R)"
        >
          {isRunningRuntime ? 'Collecting Traces...' : 'Run Runtime'}
        </Button>

        {/* AI Inspector Toggle */}
        <button
          className={`sd-top-navbar__drawer-toggle ${isAiDrawerOpen ? 'is-active' : ''}`}
          onClick={onToggleAiDrawer}
          title={isAiDrawerOpen ? 'Close AI Inspector' : 'Open AI Inspector'}
        >
          {isAiDrawerOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
        </button>
      </div>
    </header>
  )
}
