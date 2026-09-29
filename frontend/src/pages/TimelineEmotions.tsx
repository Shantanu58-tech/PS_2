import { AreaChart, Area, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useEmotions } from '../hooks/useApi'
import { useAppStore } from '../store/app'
const EMOTIONS = [
  { key: 'anxiety', color: '#ef4444' },
  { key: 'excitement', color: '#22c55e' },
  { key: 'against', color: '#f97316' },
  { key: 'supportive', color: '#3b82f6' },
  { key: 'sarcasm', color: '#a855f7' },
]
export default function TimelineEmotions() {
  const { organicOnly } = useAppStore()
  const { data } = useEmotions({ organic_only: organicOnly })
  const buckets = data?.buckets || []
  return (
    <div>
      <h1 style={{color:'white',fontSize:22,fontWeight:700,marginBottom:6}}>Timeline and Emotions</h1>
      <p style={{color:'#6b7280',fontSize:13,marginBottom:20}}>
        {organicOnly ? 'Organic only — coordinated accounts removed' : 'Raw view — toggle Organic only to see distortion removed'}
      </p>
      {buckets.length === 0 ? (
        <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:40,textAlign:'center',color:'#4b5563'}}>
          No emotion data yet — start replay scenario then wait for enrichment
        </div>
      ) : (
        <div style={{background:'#0d1326',border:'1px solid #1e2740',borderRadius:12,padding:20}}>
          <ResponsiveContainer width="100%" height={360}>
            <AreaChart data={buckets}>
              <XAxis dataKey="bucket" tick={{fill:'#9ca3af',fontSize:10}} />
              <YAxis tick={{fill:'#9ca3af',fontSize:10}} domain={[0,1]} />
              <Tooltip contentStyle={{background:'#0d1326',border:'1px solid #253454',borderRadius:8}} />
              <Legend />
              {EMOTIONS.map(e => <Area key={e.key} type="monotone" dataKey={e.key} stackId="1" stroke={e.color} fill={e.color} fillOpacity={0.25} name={e.key} />)}
            </AreaChart>
          </ResponsiveContainer>
          {organicOnly && <div style={{marginTop:12,padding:10,background:'rgba(34,197,94,0.1)',border:'1px solid #166534',borderRadius:8,fontSize:12,color:'#86efac'}}>
            Organic-only: coordinated accounts (score 0.7+) excluded.
          </div>}
        </div>
      )}
    </div>
  )
}
