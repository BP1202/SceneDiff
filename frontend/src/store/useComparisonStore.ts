import { create } from 'zustand'
import { BehaviorComparisonSummary, DiffCategory, SeverityLevel, TimelineEvent } from '../types'
import { mockComparisonSummary } from '../utils/mockData'

interface ComparisonStoreState {
  summary: BehaviorComparisonSummary
  activeCategory: DiffCategory | 'all'
  activeSeverity: SeverityLevel | 'all'
  selectedEvent: TimelineEvent | null
  setActiveCategory: (cat: DiffCategory | 'all') => void
  setActiveSeverity: (sev: SeverityLevel | 'all') => void
  setSelectedEvent: (event: TimelineEvent | null) => void
}

export const useComparisonStore = create<ComparisonStoreState>((set) => ({
  summary: mockComparisonSummary,
  activeCategory: 'all',
  activeSeverity: 'all',
  selectedEvent: mockComparisonSummary.timeline.find((t) => t.isFirstDivergence) || null,
  setActiveCategory: (activeCategory) => set({ activeCategory }),
  setActiveSeverity: (activeSeverity) => set({ activeSeverity }),
  setSelectedEvent: (selectedEvent) => set({ selectedEvent }),
}))
