import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useDemographics } from '../hooks/useApi'
import { useAppStore } from '../store/app'
const COLORS = ['#3b82f6','#22c55e','#f97316','#a855f7','#eab308','#ef4444','#06b6d4']
export default function Audience() {
  const { organicOnly } = useAppStore()
  const { data } = useDemographics(organicOnly)
  const aggregates: any[] = data?.aggregates || []
  const k = data?.k_anon || 10
  const byDim: Record<string, any[]> = aggregates.reduce((acc:any, r:any) => { if(!acc[r.dimension]) acc[r.dimension]=[]; acc[r.dimension].push({name:r.bucket,value:r.count}); return acc }, {})
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:6}}>Audience Demographics</h1>
      <div style={{background:'rgba(161,108,0,0.15)',border:'1px solid #78350f',borderRadius:8,padding:'8px 14px',marginBottom:16,fontSize:11,color:'#fcd34d'}}>
        Aggregate only k-anonymity k={k} Buckets under k suppressed No individual profiling
      </div>
      {aggregates.length === 0 ? <div style={{color:'#4b5563',fontSize:13}}>No demographic data — run replay and compute demographics</div> : (
        Object.entries(byDim).map(([dim, items]) => (
          <div key={dim} style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:20,marginBottom:16}}>
            <h3 style={{color:'white',fontWeight:600,marginBottom:16,textTransform:'capitalize'}}>{dim}</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={items} layout="vertical">
                <XAxis type="number" tick={{fill:'#9ca3af',fontSize:10}} />
                <YAxis type="category" dataKey="name" width={110} tick={{fill:'#9ca3af',fontSize:10}} />
                <Tooltip contentStyle={{background:'#0d1326',border:'1px solid #253454'}} />
                <Bar dataKey="value" radius={3}>{items.map((_:any,i:number)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}</Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ))
      )}
    </div>
  )
}
