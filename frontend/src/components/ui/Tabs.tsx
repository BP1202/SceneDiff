import React from 'react'
import './Tabs.css'

export interface TabItem {
  id: string
  label: string
  icon?: React.ReactNode
  count?: number | string
  severity?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
}

export interface TabsProps {
  tabs: TabItem[]
  activeTab: string
  onChange: (tabId: string) => void
  size?: 'sm' | 'md'
  className?: string
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  size = 'md',
  className = '',
}) => {
  return (
    <div className={`sd-tabs sd-tabs--${size} ${className}`} role="tablist">
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            className={`sd-tab-item ${isActive ? 'is-active' : ''}`}
            onClick={() => onChange(tab.id)}
          >
            {tab.icon && <span className="sd-tab-item__icon">{tab.icon}</span>}
            <span className="sd-tab-item__label">{tab.label}</span>
            {tab.count !== undefined && (
              <span className={`sd-tab-item__count ${tab.severity ? `is-${tab.severity.toLowerCase()}` : ''}`}>
                {tab.count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
