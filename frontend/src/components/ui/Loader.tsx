import React from 'react'
import { Loader2 } from 'lucide-react'
import './Loader.css'

export interface LoaderProps {
  label?: string
  size?: 'sm' | 'md' | 'lg'
  fullHeight?: boolean
}

export const Loader: React.FC<LoaderProps> = ({
  label = 'Loading analysis...',
  size = 'md',
  fullHeight = false,
}) => {
  const pixelSize = size === 'sm' ? 18 : size === 'lg' ? 36 : 24
  return (
    <div className={`sd-loader ${fullHeight ? 'is-full-height' : ''}`}>
      <Loader2 className="sd-loader__spinner animate-spin" size={pixelSize} />
      {label && <span className="sd-loader__label">{label}</span>}
    </div>
  )
}
