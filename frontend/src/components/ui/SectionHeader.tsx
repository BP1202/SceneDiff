import React from 'react'
import './SectionHeader.css'

export interface SectionHeaderProps {
  title: string
  subtitle?: string
  icon?: React.ReactNode
  badge?: React.ReactNode
  actions?: React.ReactNode
  className?: string
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  icon,
  badge,
  actions,
  className = '',
}) => {
  return (
    <div className={`sd-section-header ${className}`}>
      <div className="sd-section-header__left">
        {icon && <span className="sd-section-header__icon">{icon}</span>}
        <div className="sd-section-header__titles">
          <div className="sd-section-header__main">
            <h2 className="sd-section-header__title">{title}</h2>
            {badge && <span className="sd-section-header__badge">{badge}</span>}
          </div>
          {subtitle && <p className="sd-section-header__subtitle">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="sd-section-header__actions">{actions}</div>}
    </div>
  )
}
