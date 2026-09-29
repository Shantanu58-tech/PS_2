import { create } from 'zustand'
interface AppState {
  showBriefing: boolean
  tourActive: boolean
  tourStep: number
  organicOnly: boolean
  setShowBriefing: (v: boolean) => void
  setTourActive: (v: boolean) => void
  setTourStep: (v: number) => void
  setOrganicOnly: (v: boolean) => void
}
export const useAppStore = create<AppState>((set) => ({
  showBriefing: true,
  tourActive: false,
  tourStep: 0,
  organicOnly: false,
  setShowBriefing: (v) => set({ showBriefing: v }),
  setTourActive: (v) => set({ tourActive: v }),
  setTourStep: (v) => set({ tourStep: v }),
  setOrganicOnly: (v) => set({ organicOnly: v }),
}))
