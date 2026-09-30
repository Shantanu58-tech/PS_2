import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'

const API = '/api'

export async function getJSON<T = any>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export async function postJSON<T = any>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error((data as any)?.detail || `${res.status} ${res.statusText}`)
  return data as T
}

// Hold the previous render while refetching (no skeleton flash on filter changes).
const q = <T,>(key: unknown[], url: string, extra: Record<string, unknown> = {}) =>
  useQuery<T>({ queryKey: key, queryFn: () => getJSON<T>(url), placeholderData: keepPreviousData, ...extra })

export const useHealth = () => q<any>(['health'], '/healthz', { refetchInterval: 20000 })
export const useAlerts = () => q<any>(['alerts'], `${API}/alerts`, { refetchInterval: 30000 })
export const useTopics = (sort = 'volume', limit = 50) => q<any>(['topics', sort, limit], `${API}/topics?sort=${sort}&limit=${limit}`)
export const useTopic = (id?: number) => useQuery<any>({ queryKey: ['topic', id], queryFn: () => getJSON(`${API}/topics/${id}`), enabled: id != null })
export const useTopicSeries = (id?: number) => useQuery<any>({ queryKey: ['series', id], queryFn: () => getJSON(`${API}/topics/${id}/series`), enabled: id != null })
export const useEmotions = (organic: boolean, bucket = '1h', topicId?: number, platform = '', kind = 'all') =>
  q<any>(['emotions', organic, bucket, topicId, platform, kind],
    `${API}/timeline/emotions?bucket=${bucket}&organic_only=${organic}&kind=${kind}${topicId != null ? `&topic_id=${topicId}` : ''}${platform ? `&platform=${platform}` : ''}`)
export const useVolume = (bucket = '1h', platform = '') => q<any>(['volume', bucket, platform], `${API}/timeline/volume?bucket=${bucket}${platform ? `&platform=${platform}` : ''}`)
export const useSituation = () => q<any>(['situation'], `${API}/situation`, { refetchInterval: 60000 })
export const useNode = (id?: string | null) => useQuery<any>({ queryKey: ['node', id], queryFn: () => getJSON(`${API}/graph/node/${encodeURIComponent(id!)}`), enabled: !!id })
export const usePlatforms = () => q<any>(['platforms'], `${API}/platforms`, { refetchInterval: 60000 })
export const usePlatform = (p?: string) => useQuery<any>({ queryKey: ['platform', p], queryFn: () => getJSON(`${API}/platforms/${p}`), enabled: !!p, placeholderData: keepPreviousData })
export const useKeywords = () => q<any>(['keywords'], `${API}/keywords/trending?limit=10`)
export const useSegmentSpread = (topicId?: number) => q<any>(['segment-spread', topicId], `${API}/graph/segment-spread${topicId != null ? `?topic_id=${topicId}` : ''}`)
export const useCompare = (topicId?: number, platform = '', kind = 'all') => q<any>(['compare', topicId, platform, kind],
  `${API}/timeline/compare?kind=${kind}${topicId != null ? `&topic_id=${topicId}` : ''}${platform ? `&platform=${platform}` : ''}`)
export const useGraph = (organic: boolean, maxNodes = 220) => q<any>(['graph', organic, maxNodes], `${API}/graph?organic_only=${organic}&max_nodes=${maxNodes}`)
export const useInfluencers = (organic: boolean, limit = 15) => q<any>(['influencers', organic, limit], `${API}/influencers?organic_only=${organic}&limit=${limit}`)
export const useSpread = (topicId?: number) => q<any>(['spread', topicId], `${API}/graph/spread${topicId != null ? `?topic_id=${topicId}` : ''}`)
export const useClusters = () => q<any>(['clusters'], `${API}/coordination/clusters`)
export const useCluster = (id?: number) => useQuery<any>({ queryKey: ['cluster', id], queryFn: () => getJSON(`${API}/coordination/clusters/${id}`), enabled: id != null })
export const useBehaviour = () => q<any>(['behaviour'], `${API}/behaviour?limit=20`)
export const useDemographics = (organic: boolean) => q<any>(['demographics', organic], `${API}/demographics?organic_only=${organic}`)
export const useLineage = () => q<any>(['lineage'], `${API}/lineage`)
export const useLedgerStatus = () => q<any>(['ledger-status'], `${API}/ledger/status`, { refetchInterval: 30000 })
export const useCheckpoints = () => q<any>(['checkpoints'], `${API}/ledger/checkpoints?limit=12`)
export const useAudit = () => q<any>(['audit'], `${API}/audit?limit=20`)
export const useCases = () => q<any>(['cases'], `${API}/cases`)
export const useEvalSummary = () => q<any>(['eval'], `${API}/eval/summary`, { staleTime: 5 * 60_000 })
export const useTraceability = () => q<any>(['traceability'], `${API}/traceability`, { staleTime: 5 * 60_000 })
export const useCollectors = () => q<any>(['collectors'], `${API}/collectors`, { refetchInterval: 20000 })
export const useSummary = (topicId?: number) => useQuery<any>({ queryKey: ['summary', topicId], queryFn: () => getJSON(`${API}/summaries/topic/${topicId}`), enabled: topicId != null })

export function useCreateCase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (b: { alert_id: number; title: string }) => postJSON(`${API}/cases`, b),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cases'] }); qc.invalidateQueries({ queryKey: ['alerts'] }); qc.invalidateQueries({ queryKey: ['audit'] }) },
  })
}

export function useSummarize(topicId?: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => postJSON(`${API}/summaries/topic/${topicId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['summary', topicId] }),
  })
}

export function useReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ alertId, action }: { alertId: number; action: 'approve' | 'watchlist' | 'dismiss' }) =>
      postJSON(`${API}/alerts/${alertId}/review`, { action }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts'] })
      qc.invalidateQueries({ queryKey: ['situation'] })
      qc.invalidateQueries({ queryKey: ['cases'] })
      qc.invalidateQueries({ queryKey: ['audit'] })
    },
  })
}
