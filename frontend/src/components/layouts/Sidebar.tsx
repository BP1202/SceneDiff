import React from 'react'
import {
  LayoutDashboard,
  PlayCircle,
  GitCompare,
  BrainCircuit,
  Wrench,
  Download,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Terminal,
} from 'lucide-react'
import './Sidebar.css'

export type NavView = 'dashboard' | 'runtime' | 'comparison' | 'rootcause' | 'repair' | 'export'

export interface SidebarProps {
  currentView: NavView
  onSelectView: (view: NavView) => void
  isCollapsed: boolean
  onToggleCollapse: () => void
  regressionsCount?: number
  pendingRepairsCount?: number
}

interface NavItem {
  id: NavView
  label: string
  icon: React.ReactNode
  badge?: string
  badgeSeverity?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
  accent?: boolean
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onSelectView,
  isCollapsed,
  onToggleCollapse,
  regressionsCount = 0,
  pendingRepairsCount = 0,
}) => {
  const navItems: NavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'runtime', label: 'Runtime Collector', icon: <PlayCircle size={18} /> },
    {
      id: 'comparison',
      label: 'Behavior Diff',
      icon: <GitCompare size={18} />,
      badge: regressionsCount > 0 ? `${regressionsCount}` : undefined,
      badgeSeverity: 'CRITICAL',
    },
    {
      id: 'rootcause',
      label: 'Root Cause AI',
      icon: <BrainCircuit size={18} />,
      accent: true,
    },
    {
      id: 'repair',
      label: 'Repair Studio',
      icon: <Wrench size={18} />,
      badge: pendingRepairsCount > 0 ? `${pendingRepairsCount}` : undefined,
      badgeSeverity: 'HIGH',
    },
    { id: 'export', label: 'Export Center', icon: <Download size={18} /> },
  ]

  return (
    <aside className={`sd-sidebar ${isCollapsed ? 'is-collapsed' : ''}`}>
      {/* Brand Header */}
      <div className="sd-sidebar__brand">
        <div className="sd-sidebar__logo">
          <Terminal size={20} className="sd-sidebar__logo-icon" />
          <div className="sd-sidebar__status-dot" title="IBM Bob Connected" />
        </div>
        {!isCollapsed && (
          <div className="sd-sidebar__brand-text">
            <span className="sd-sidebar__title">SceneDiff</span>
            <span className="sd-sidebar__version">Bob 2.0 AI</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="sd-sidebar__nav">
        {navItems.map((item) => {
          const isActive = currentView === item.id
          return (
            <button
              key={item.id}
              className={`sd-sidebar__item ${isActive ? 'is-active' : ''} ${item.accent ? 'is-accent' : ''}`}
              onClick={() => onSelectView(item.id)}
              title={isCollapsed ? item.label : undefined}
            >
              <span className="sd-sidebar__item-icon">{item.icon}</span>
              {!isCollapsed && <span className="sd-sidebar__item-label">{item.label}</span>}
              {!isCollapsed && item.badge && (
                <span className={`sd-sidebar__item-badge is-${item.badgeSeverity?.toLowerCase() || 'default'}`}>
                  {item.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Secret Shield Compliance Badge */}
      {!isCollapsed && (
        <div className="sd-sidebar__shield">
          <ShieldCheck size={16} className="sd-sidebar__shield-icon" />
          <div className="sd-sidebar__shield-content">
            <span className="sd-sidebar__shield-title">Secret Shield Active</span>
            <span className="sd-sidebar__shield-subtitle">Traces Auto-Masked</span>
          </div>
        </div>
      )}

      {/* Collapse Toggle Footer */}
      <div className="sd-sidebar__footer">
        <button
          className="sd-sidebar__collapse-btn"
          onClick={onToggleCollapse}
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          {!isCollapsed && <span className="sd-sidebar__collapse-label">Collapse</span>}
        </button>
      </div>
    </aside>
  )
}
