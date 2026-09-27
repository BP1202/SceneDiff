import React from 'react'
import './Card.css'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'interactive' | 'outline'
  glow?: boolean
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  glow = false,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`sd-card sd-card--${variant} ${glow ? 'is-glowing' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => <div className={`sd-card__header ${className}`} {...props}>{children}</div>

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className = '',
  ...props
}) => <h3 className={`sd-card__title ${className}`} {...props}>{children}</h3>

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => <div className={`sd-card__content ${className}`} {...props}>{children}</div>

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => <div className={`sd-card__footer ${className}`} {...props}>{children}</div>
