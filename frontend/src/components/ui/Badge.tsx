import React from 'react'
import './Badge.css'

export type BadgeSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO' | 'SUCCESS' | 'DEFAULT'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  severity?: BadgeSeverity
  size?: 'sm' | 'md'
  dot?: boolean
  glow?: boolean
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  severity = 'DEFAULT',
  size = 'md',
  dot = false,
  glow = false,
  className = '',
  ...props
}) => {
  const sevKey = severity.toLowerCase()
  return (
    <span
      className={`sd-badge sd-badge--${sevKey} sd-badge--${size} ${glow ? 'is-glowing' : ''} ${className}`}
      {...props}
    >
      {dot && <span className="sd-badge__dot" />}
      <span className="sd-badge__text">{children}</span>
    </span>
  )
}
