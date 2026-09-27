import React, { useEffect } from 'react'
import { X } from 'lucide-react'
import './Modal.css'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  subtitle?: string
  children: React.ReactNode
  footer?: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  size = 'md',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="sd-modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className={`sd-modal sd-modal--${size} glass-panel`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sd-modal__header">
          <div>
            <h3 className="sd-modal__title">{title}</h3>
            {subtitle && <p className="sd-modal__subtitle">{subtitle}</p>}
          </div>
          <button className="sd-modal__close" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>
        <div className="sd-modal__body">{children}</div>
        {footer && <div className="sd-modal__footer">{footer}</div>}
      </div>
    </div>
  )
}
