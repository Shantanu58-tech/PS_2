import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export interface PipelineStatus {
  replay: { state: string; ingested: number; total: number }
  analytics: { state: string; stage: string | null; error?: string | null }
}

/** Live pipeline progress over SSE (/api/stream). Refreshes data when analytics finish. */
export function useLiveStatus(): PipelineStatus | null {
  const [status, setStatus] = useState<PipelineStatus | null>(null)
  const qc = useQueryClient()
  useEffect(() => {
    let es: EventSource | null = null
    try {
      es = new EventSource('/api/stream')
    } catch {
      return
    }
    const onStatus = (e: MessageEvent) => {
      try { setStatus(JSON.parse(e.data)) } catch { /* ignore */ }
    }
    const onSection = (section: 'replay' | 'analytics') => (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data)
        setStatus(prev => ({ ...(prev ?? { replay: {} as any, analytics: {} as any }), [section]: data }))
        if (section === 'analytics' && data.state === 'done') qc.invalidateQueries()
      } catch { /* ignore */ }
    }
    es.addEventListener('status', onStatus)
    es.addEventListener('replay_status', onSection('replay'))
    es.addEventListener('analytics_status', onSection('analytics'))
    return () => es?.close()
  }, [qc])
  return status
}
