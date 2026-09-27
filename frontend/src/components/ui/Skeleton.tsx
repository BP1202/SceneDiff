import React from 'react'
import './Skeleton.css'

export interface SkeletonProps {
  width?: string | number
  height?: string | number
  borderRadius?: string | number
  className?: string
  count?: number
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = 16,
  borderRadius = 4,
  className = '',
  count = 1,
}) => {
  const items = Array.from({ length: count }, (_, i) => i)

  return (
    <div className={`sd-skeleton-group ${className}`}>
      {items.map((key) => (
        <div
          key={key}
          className="sd-skeleton"
          style={{
            width: typeof width === 'number' ? `${width}px` : width,
            height: typeof height === 'number' ? `${height}px` : height,
            borderRadius: typeof borderRadius === 'number' ? `${borderRadius}px` : borderRadius,
          }}
        />
      ))}
    </div>
  )
}
