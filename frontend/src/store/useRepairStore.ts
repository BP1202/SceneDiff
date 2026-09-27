import { create } from 'zustand'
import { RepairReportData } from '../types'
import { mockRepairReport } from '../utils/mockData'

interface RepairStoreState {
  repair: RepairReportData
  approveRepair: () => void
  rejectRepair: () => void
  setRepair: (repair: RepairReportData) => void
}

export const useRepairStore = create<RepairStoreState>((set) => ({
  repair: mockRepairReport,
  approveRepair: () =>
    set((state) => ({ repair: { ...state.repair, status: 'approved' } })),
  rejectRepair: () =>
    set((state) => ({ repair: { ...state.repair, status: 'rejected' } })),
  setRepair: (repair) => set({ repair }),
}))
