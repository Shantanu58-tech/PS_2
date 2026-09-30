import { create } from 'zustand'

type Theme = 'dark' | 'light'

function load<T>(key: string, fallback: T): T {
  try {
    const v = localStorage.getItem(key)
    return v === null ? fallback : (JSON.parse(v) as T)
  } catch {
    return fallback
  }
}
function save(key: string, v: unknown) {
  try { localStorage.setItem(key, JSON.stringify(v)) } catch { /* private mode: ignore */ }
}

interface AppState {
  showBriefing: boolean
  tourActive: boolean
  tourStep: number
  organicOnly: boolean
  theme: Theme
  navOpen: boolean
  navCollapsed: boolean
  setNavCollapsed: (v: boolean) => void
  setShowBriefing: (v: boolean) => void
  setTourActive: (v: boolean) => void
  setTourStep: (v: number) => void
  setOrganicOnly: (v: boolean) => void
  setTheme: (t: Theme) => void
  setNavOpen: (v: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
  showBriefing: false,  // the landing page introduces the product; About re-opens this
  tourActive: false,
  tourStep: 0,
  organicOnly: load('deepastambha.organicOnly', false),
  theme: load<Theme>('deepastambha.theme', 'light'),
  navOpen: false,
  navCollapsed: load('deepastambha.navCollapsed', false),
  setNavCollapsed: (v) => { save('deepastambha.navCollapsed', v); set({ navCollapsed: v }) },
  setShowBriefing: (v) => { if (!v) save('deepastambha.briefingSeen', true); set({ showBriefing: v }) },
  setTourActive: (v) => set({ tourActive: v, tourStep: v ? 0 : 0 }),
  setTourStep: (v) => set({ tourStep: v }),
  setOrganicOnly: (v) => { save('deepastambha.organicOnly', v); set({ organicOnly: v }) },
  setTheme: (t) => { save('deepastambha.theme', t); document.documentElement.setAttribute('data-theme', t); set({ theme: t }) },
  setNavOpen: (v) => set({ navOpen: v }),
}))

// apply persisted theme before first paint of React tree
document.documentElement.setAttribute('data-theme', load<Theme>('deepastambha.theme', 'light'))
