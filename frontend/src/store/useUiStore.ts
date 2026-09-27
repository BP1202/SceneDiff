import { create } from 'zustand'
import { NavView } from '../components/layouts/Sidebar'

interface UiStoreState {
  currentView: NavView
  isAiDrawerOpen: boolean
  setCurrentView: (view: NavView) => void
  toggleAiDrawer: () => void
  setAiDrawerOpen: (isOpen: boolean) => void
}

export const useUiStore = create<UiStoreState>((set) => ({
  currentView: 'dashboard',
  isAiDrawerOpen: true,
  setCurrentView: (currentView) => set({ currentView }),
  toggleAiDrawer: () => set((state) => ({ isAiDrawerOpen: !state.isAiDrawerOpen })),
  setAiDrawerOpen: (isAiDrawerOpen) => set({ isAiDrawerOpen }),
}))
