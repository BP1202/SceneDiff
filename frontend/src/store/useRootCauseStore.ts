import { create } from 'zustand'
import { RootCauseReport, EvidenceNode } from '../types'
import { mockRootCauseReport } from '../utils/mockData'

interface RootCauseStoreState {
  report: RootCauseReport
  selectedNode: EvidenceNode | null
  setSelectedNode: (node: EvidenceNode | null) => void
}

export const useRootCauseStore = create<RootCauseStoreState>((set) => ({
  report: mockRootCauseReport,
  selectedNode: mockRootCauseReport.evidenceNodes.find((n) => n.id === 'node-code') || null,
  setSelectedNode: (selectedNode) => set({ selectedNode }),
}))
