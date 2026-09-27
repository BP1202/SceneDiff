import { create } from 'zustand'
import { RuntimeExecution, RuntimeStatus, RuntimeTraceLog } from '../types'
import { mockRuntimeExecution } from '../utils/mockData'

interface RuntimeStoreState {
  execution: RuntimeExecution
  isRunning: boolean
  startExecution: () => void
  addLog: (log: Omit<RuntimeTraceLog, 'id'>) => void
  setStatus: (status: RuntimeStatus) => void
  finishExecution: () => void
  reset: () => void
}

export const useRuntimeStore = create<RuntimeStoreState>((set) => ({
  execution: mockRuntimeExecution,
  isRunning: false,
  startExecution: () =>
    set({
      isRunning: true,
      execution: {
        ...mockRuntimeExecution,
        status: 'launching_browser',
        durationMs: 0,
        logs: [
          {
            id: '1',
            timestamp: '00:00.000',
            level: 'info',
            message: 'Initializing headless Playwright Chromium instance...',
            phase: 'browser',
          },
        ],
      },
    }),
  addLog: (log) =>
    set((state) => ({
      execution: {
        ...state.execution,
        logs: [
          ...state.execution.logs,
          { ...log, id: `${state.execution.logs.length + 1}` },
        ],
      },
    })),
  setStatus: (status) =>
    set((state) => ({
      execution: { ...state.execution, status },
    })),
  finishExecution: () =>
    set((state) => ({
      isRunning: false,
      execution: {
        ...state.execution,
        status: 'completed',
        durationMs: 1420,
      },
    })),
  reset: () =>
    set({
      isRunning: false,
      execution: mockRuntimeExecution,
    }),
}))
