import React from 'react'
import './GlassPanel.css'

export interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: boolean
}

export const GlassPanel: React.FC<GlassPanelProps> = ({
  children,
  glow = false,
  className = '',
  ...props
}) => {
  return (
    <div className={`sd-glass-panel ${glow ? 'is-glowing' : ''} ${className}`} {...props}>
      {children}
    </div>
  )
}
