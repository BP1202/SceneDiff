import React, { useState, useEffect } from 'react'
import {
  Search,
  Play,
  GitCompare,
  BrainCircuit,
  Wrench,
  Download,
  FileCode,
} from 'lucide-react'
import { Modal } from '../ui/Modal'
import { NavView } from './Sidebar'
import './CommandPalette.css'

export interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  onSelectView: (view: NavView) => void
  onRunRuntime: () => void
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectView,
  onRunRuntime,
}) => {
  const [query, setQuery] = useState('')

  useEffect(() => {
    if (isOpen) setQuery('')
  }, [isOpen])

  const commands = [
    {
      id: 'run-runtime',
      label: 'Run Playwright Runtime Collector',
      category: 'Actions',
      icon: <Play size={16} />,
      action: () => {
        onRunRuntime()
        onClose()
      },
    },
    {
      id: 'goto-timeline',
      label: 'Go to Behavior Timeline & First Divergence',
      category: 'Navigation',
      icon: <GitCompare size={16} />,
      action: () => {
        onSelectView('comparison')
        onClose()
      },
    },
    {
      id: 'goto-rootcause',
      label: 'Inspect Root Cause Causal Graph',
      category: 'Navigation',
      icon: <BrainCircuit size={16} />,
      action: () => {
        onSelectView('rootcause')
        onClose()
      },
    },
    {
      id: 'goto-repair',
      label: 'Open Repair Studio & Unified Patch',
      category: 'Navigation',
      icon: <Wrench size={16} />,
      action: () => {
        onSelectView('repair')
        onClose()
      },
    },
    {
      id: 'goto-export',
      label: 'Export Evidence & GitHub PR Summary',
      category: 'Navigation',
      icon: <Download size={16} />,
      action: () => {
        onSelectView('export')
        onClose()
      },
    },
    {
      id: 'inspect-culprit',
      label: 'Inspect Culprit File: app/auth/login.py',
      category: 'Files',
      icon: <FileCode size={16} />,
      action: () => {
        onSelectView('repair')
        onClose()
      },
    },
  ]

  const filtered = commands.filter((cmd) =>
    cmd.label.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Command Palette" size="md">
      <div className="sd-cmd-palette">
        <div className="sd-cmd-palette__search">
          <Search size={16} className="sd-cmd-palette__search-icon" />
          <input
            type="text"
            className="sd-cmd-palette__input"
            placeholder="Type a command or search workspace..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>
        <div className="sd-cmd-palette__list">
          {filtered.length === 0 ? (
            <div className="sd-cmd-palette__empty">No matching commands found.</div>
          ) : (
            filtered.map((cmd) => (
              <button
                key={cmd.id}
                className="sd-cmd-palette__item"
                onClick={cmd.action}
              >
                <span className="sd-cmd-palette__item-icon">{cmd.icon}</span>
                <span className="sd-cmd-palette__item-label">{cmd.label}</span>
                <span className="sd-cmd-palette__item-cat">{cmd.category}</span>
              </button>
            ))
          )}
        </div>
        <div className="sd-cmd-palette__footer">
          <span>Navigate with <kbd>↑</kbd> <kbd>↓</kbd></span>
          <span>Execute with <kbd>Enter</kbd></span>
          <span>Close with <kbd>Esc</kbd></span>
        </div>
      </div>
    </Modal>
  )
}
