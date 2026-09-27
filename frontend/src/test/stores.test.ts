import { describe, it, expect, beforeEach } from 'vitest'
import { act } from '@testing-library/react'

import { useRepositoryStore } from '../../store/useRepositoryStore'
import { useComparisonStore } from '../../store/useComparisonStore'
import { useUiStore } from '../../store/useUiStore'
import { useRepairStore } from '../../store/useRepairStore'
import { useRootCauseStore } from '../../store/useRootCauseStore'

describe('useRepositoryStore', () => {
  it('has default repository state', () => {
    const { repository } = useRepositoryStore.getState()
    expect(repository).toBeDefined()
    expect(repository.name).toBeTruthy()
    expect(repository.baseCommit.sha).toBeTruthy()
    expect(repository.headCommit.sha).toBeTruthy()
  })

  it('setTarget updates name and commits', () => {
    const store = useRepositoryStore.getState()
    act(() => {
      store.setTarget('my-repo', 'abc1234abc1234', 'def5678def5678')
    })
    const updated = useRepositoryStore.getState()
    expect(updated.repository.name).toBe('my-repo')
    expect(updated.repository.baseCommit.sha).toBe('abc1234abc1234')
    expect(updated.repository.headCommit.sha).toBe('def5678def5678')
    expect(updated.repository.baseCommit.shortSha).toBe('abc1234')
    expect(updated.repository.headCommit.shortSha).toBe('def5678')
  })

  it('setRepositoryUrl updates url only', () => {
    act(() => {
      useRepositoryStore.getState().setRepositoryUrl('https://github.com/test/repo')
    })
    expect(useRepositoryStore.getState().repository.url).toBe('https://github.com/test/repo')
  })
})

describe('useComparisonStore', () => {
  it('has default filter state', () => {
    const state = useComparisonStore.getState()
    expect(state.activeCategory).toBe('all')
    expect(state.activeSeverity).toBe('all')
  })

  it('setActiveCategory updates filter', () => {
    act(() => {
      useComparisonStore.getState().setActiveCategory('dom')
    })
    expect(useComparisonStore.getState().activeCategory).toBe('dom')
  })

  it('setActiveSeverity updates severity filter', () => {
    act(() => {
      useComparisonStore.getState().setActiveSeverity('CRITICAL')
    })
    expect(useComparisonStore.getState().activeSeverity).toBe('CRITICAL')
  })

  it('setSelectedEvent updates selected event', () => {
    act(() => {
      useComparisonStore.getState().setSelectedEvent(null)
    })
    expect(useComparisonStore.getState().selectedEvent).toBeNull()
  })
})

describe('useUiStore', () => {
  it('starts on dashboard view', () => {
    const state = useUiStore.getState()
    expect(state.currentView).toBe('dashboard')
  })

  it('setCurrentView switches view', () => {
    act(() => {
      useUiStore.getState().setCurrentView('comparison')
    })
    expect(useUiStore.getState().currentView).toBe('comparison')
    act(() => {
      useUiStore.getState().setCurrentView('dashboard')
    })
  })
})

describe('useRepairStore', () => {
  it('has initial repair state', () => {
    const { repair } = useRepairStore.getState()
    expect(repair).toBeDefined()
    expect(repair.status).toBeTruthy()
    expect(repair.risk).toBeDefined()
    expect(repair.risk.level).toBeTruthy()
  })
})

describe('useRootCauseStore', () => {
  it('has initial report with primary candidate', () => {
    const { report } = useRootCauseStore.getState()
    expect(report).toBeDefined()
    expect(report.primaryCandidate).toBeDefined()
    expect(report.primaryCandidate.file).toBeTruthy()
    expect(typeof report.rootCauseConfidence).toBe('number')
  })
})
