import React from 'react'
import './EmptyState.css'
import { Button } from './Button'

export interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div className="sd-empty-state">
      {icon && <div className="sd-empty-state__icon">{icon}</div>}
      <h4 className="sd-empty-state__title">{title}</h4>
      {description && <p className="sd-empty-state__desc">{description}</p>}
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  )
}
