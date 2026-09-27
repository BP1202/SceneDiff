import React from 'react'
import './Button.css'
import { Loader2 } from 'lucide-react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost' | 'cyan'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  icon?: React.ReactNode
  iconRight?: React.ReactNode
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  iconRight,
  className = '',
  disabled,
  ...props
}) => {
  return (
    <button
      className={`sd-button sd-button--${variant} sd-button--${size} ${className} ${isLoading ? 'is-loading' : ''}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="sd-button__spinner animate-spin" size={size === 'sm' ? 14 : 16} />
      ) : (
        icon && <span className="sd-button__icon-left">{icon}</span>
      )}
      <span className="sd-button__content">{children}</span>
      {!isLoading && iconRight && <span className="sd-button__icon-right">{iconRight}</span>}
    </button>
  )
}
