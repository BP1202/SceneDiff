import React, { useState } from 'react'
import { GitBranch, GitCommit, Check } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import './RepoSelectorModal.css'

export interface RepoSelectorModalProps {
  isOpen: boolean
  onClose: () => void
  currentRepo: string
  currentBaseCommit: string
  currentHeadCommit: string
  onSave: (repo: string, base: string, head: string) => void
}

export const RepoSelectorModal: React.FC<RepoSelectorModalProps> = ({
  isOpen,
  onClose,
  currentRepo,
  currentBaseCommit,
  currentHeadCommit,
  onSave,
}) => {
  const [repo, setRepo] = useState(currentRepo)
  const [baseCommit, setBaseCommit] = useState(currentBaseCommit)
  const [headCommit, setHeadCommit] = useState(currentHeadCommit)

  const samplePresets = [
    {
      name: 'BP1202/SceneDiff (JWT Auth Regression)',
      repo: 'BP1202/SceneDiff',
      base: 'f4a180d297',
      head: 'e93b11c841',
    },
    {
      name: 'Sample E-Commerce (Checkout Cart Crash)',
      repo: 'demo/ecommerce-store',
      base: 'a1b2c3d4e5',
      head: 'b2c3d4e5f6',
    },
  ]

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(repo, baseCommit, headCommit)
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Repository & Commit Target"
      subtitle="Select the Git repository and commits to compare for behavior regressions."
      size="md"
    >
      <form onSubmit={handleApply} className="sd-repo-modal">
        {/* Presets */}
        <div className="sd-repo-modal__presets">
          <label className="sd-repo-modal__label">Quick Presets</label>
          <div className="sd-repo-modal__preset-list">
            {samplePresets.map((preset) => (
              <button
                type="button"
                key={preset.name}
                className="sd-repo-modal__preset-btn"
                onClick={() => {
                  setRepo(preset.repo)
                  setBaseCommit(preset.base)
                  setHeadCommit(preset.head)
                }}
              >
                <span>{preset.name}</span>
                <code>{preset.base.slice(0, 7)} → {preset.head.slice(0, 7)}</code>
              </button>
            ))}
          </div>
        </div>

        {/* Inputs */}
        <div className="sd-repo-modal__field">
          <label className="sd-repo-modal__label">Repository URL / Path</label>
          <div className="sd-repo-modal__input-wrapper">
            <GitBranch size={16} className="sd-repo-modal__input-icon" />
            <input
              type="text"
              className="sd-repo-modal__input"
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              placeholder="e.g. BP1202/SceneDiff"
              required
            />
          </div>
        </div>

        <div className="sd-repo-modal__row">
          <div className="sd-repo-modal__field">
            <label className="sd-repo-modal__label">Base Commit A (Baseline)</label>
            <div className="sd-repo-modal__input-wrapper">
              <GitCommit size={16} className="sd-repo-modal__input-icon" />
              <input
                type="text"
                className="sd-repo-modal__input font-mono"
                value={baseCommit}
                onChange={(e) => setBaseCommit(e.target.value)}
                placeholder="SHA or tag"
                required
              />
            </div>
          </div>

          <div className="sd-repo-modal__field">
            <label className="sd-repo-modal__label">Head Commit B (Under Review)</label>
            <div className="sd-repo-modal__input-wrapper">
              <GitCommit size={16} className="sd-repo-modal__input-icon" />
              <input
                type="text"
                className="sd-repo-modal__input font-mono"
                value={headCommit}
                onChange={(e) => setHeadCommit(e.target.value)}
                placeholder="SHA or tag"
                required
              />
            </div>
          </div>
        </div>

        <div className="sd-repo-modal__footer">
          <Button variant="ghost" size="sm" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" type="submit" icon={<Check size={14} />}>
            Apply Target
          </Button>
        </div>
      </form>
    </Modal>
  )
}
