import React from 'react'
import './MetricCard.css'

export interface MetricCardProps {
  title: string
  value: string | number
  subtext?: string
  trend?: {
    value: string
    isPositive?: boolean
  }
  icon?: React.ReactNode
  accentColor?: 'primary' | 'cyan' | 'critical' | 'warning' | 'success'
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtext,
  trend,
  icon,
  accentColor = 'primary',
}) => {
  return (
    <div className={`sd-metric-card sd-metric-card--${accentColor}`}>
      <div className="sd-metric-card__header">
        <span className="sd-metric-card__title">{title}</span>
        {icon && <span className="sd-metric-card__icon">{icon}</span>}
      </div>
      <div className="sd-metric-card__value-row">
        <span className="sd-metric-card__value">{value}</span>
        {trend && (
          <span className={`sd-metric-card__trend ${trend.isPositive ? 'is-positive' : 'is-negative'}`}>
            {trend.value}
          </span>
        )}
      </div>
      {subtext && <p className="sd-metric-card__subtext">{subtext}</p>}
    </div>
  )
}
