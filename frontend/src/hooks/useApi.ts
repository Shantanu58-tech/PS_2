import { useQuery } from '@tanstack/react-query'
const API = '/api'
async function get(url: string) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json()
}
export const useHealth = () => useQuery({ queryKey: ['health'], queryFn: () => get(`${API}/healthz`), refetchInterval: 10000 })
export const useAlerts = (organicOnly = false) => useQuery({ queryKey: ['alerts', organicOnly], queryFn: () => get(`${API}/alerts`), refetchInterval: 15000 })
export const useTopics = () => useQuery({ queryKey: ['topics'], queryFn: () => get(`${API}/topics`), refetchInterval: 60000 })
export const useEmotions = (p: any = {}) => useQuery({ queryKey: ['emotions', p], queryFn: () => get(`${API}/timeline/emotions?organic_only=${p.organic_only || false}`) })
export const useGraph = (o = false) => useQuery({ queryKey: ['graph', o], queryFn: () => get(`${API}/graph?organic_only=${o}`) })
export const useInfluencers = () => useQuery({ queryKey: ['influencers'], queryFn: () => get(`${API}/influencers`) })
export const useClusters = () => useQuery({ queryKey: ['clusters'], queryFn: () => get(`${API}/coordination/clusters`) })
export const useDemographics = (o = false) => useQuery({ queryKey: ['demographics', o], queryFn: () => get(`${API}/demographics?organic_only=${o}`) })
export const useLedgerStatus = () => useQuery({ queryKey: ['ledger-status'], queryFn: () => get(`${API}/ledger/status`), refetchInterval: 30000 })
export const useEvalSummary = () => useQuery({ queryKey: ['eval'], queryFn: () => get(`${API}/eval/summary`) })
export const useTraceability = () => useQuery({ queryKey: ['traceability'], queryFn: () => get(`${API}/traceability`) })
export const useCollectors = () => useQuery({ queryKey: ['collectors'], queryFn: () => get(`${API}/collectors`), refetchInterval: 10000 })
export const usePosts = (p: any = {}) => useQuery({ queryKey: ['posts', p], queryFn: () => get(`${API}/posts?limit=${p.limit || 50}`) })
