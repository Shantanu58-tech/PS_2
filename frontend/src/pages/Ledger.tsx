import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Bitcoin, Bomb, KeyRound, Lock, Search as SearchIcon, ShieldCheck, Stamp } from 'lucide-react'
import { getJSON, postJSON, useAudit, useCheckpoints, useLedgerStatus } from '../hooks/useApi'
import { Card, InfoPop, Kpi, NextStep, PageHead, StatusBadge } from '../components/ui'
import { ist, num } from '../lib/fmt'

const short = (h?: string) => (h ? `${h.slice(0, 10)}…${h.slice(-6)}` : '—')

export default function Ledger() {
  const qc = useQueryClient()
  const { data: status } = useLedgerStatus()
  const { data: cps } = useCheckpoints()
  const { data: audit } = useAudit()
  const [verify, setVerify] = useState<any>(null)
  const [tamper, setTamper] = useState<any>(null)
  const [busy, setBusy] = useState<'' | 'verify' | 'tamper' | 'proof'>('')
  const [err, setErr] = useState('')
  const [seq, setSeq] = useState('150')
  const [proof, setProof] = useState<any>(null)

  const run = async (kind: 'verify' | 'tamper') => {
    setBusy(kind); setErr('')
    try {
      if (kind === 'verify') setVerify(await postJSON('/api/ledger/verify'))
      else setTamper(await postJSON('/api/ledger/tamper-sim'))
      qc.invalidateQueries({ queryKey: ['audit'] })
    } catch (e) { setErr(String((e as Error).message)) } finally { setBusy('') }
  }
  const lookup = async () => {
    setBusy('proof'); setErr(''); setProof(null)
    try { setProof(await getJSON(`/api/ledger/proof/${Number(seq)}`)) } catch (e) { setErr(`No proof for seq ${seq}: ${(e as Error).message}`) } finally { setBusy('') }
  }

  return (
    <div>
      <PageHead title="Evidence ledger" sub="Every post is sealed the moment it arrives, so any later change is caught." />
      <div className="grid g-3" style={{ marginBottom: 24 }}>
        <Kpi icon={<Lock size={20} />} label="Posts sealed" value={num(status?.record_count)} foot="each chained to the one before"
          info={<>Every post is fingerprinted (SHA-256) and linked to the previous one, so changing any post breaks the chain from that point on.</>} />
        <Kpi icon={<Stamp size={20} />} label="Signed seals" value={num(status?.checkpoint_count)} foot="one for every 100 posts"
          info={<>Every 100 posts are rolled into a single Merkle root and digitally signed (Ed25519).</>} />
        <Kpi icon={<Bitcoin size={20} />} label="Bitcoin anchor" value={<span style={{ textTransform: 'capitalize' }}>{status?.last_checkpoint?.ots_status ?? (status?.ots_enabled ? 'enabled' : 'off')}</span>} foot="via OpenTimestamps"
          info={<>The newest seal is timestamped on the Bitcoin blockchain, proving the evidence existed at that time.</>} />
      </div>

      <div className="grid g-2" style={{ marginBottom: 16 }}>
        <Card title="Verify integrity" sub="re-check every post, link and signed seal">
          <button className="btn btn-primary" disabled={!!busy} onClick={() => run('verify')}><ShieldCheck size={15} />{busy === 'verify' ? 'Verifying…' : 'Verify integrity'}</button>
          {verify && (
            <div style={{ marginTop: 12 }}>
              {verify.status === 'PASS'
                ? <StatusBadge status="good">VERIFICATION PASSED</StatusBadge>
                : <StatusBadge status="critical">VERIFICATION FAILED</StatusBadge>}
              <div className="secondary" style={{ marginTop: 8, fontSize: 13 }}>
                {num(verify.records)} posts and {num(verify.checkpoints)} seals checked in {verify.seconds}s.
                {verify.status !== 'PASS' && <> First failure at post #{verify.seq}: {verify.reason}.</>}
              </div>
            </div>
          )}
        </Card>
        <Card title="Tamper test" sub="change one character in a copy and watch it get caught"
          actions={<InfoPop>The real ledger is never touched: the test runs on a temporary copy that is deleted afterwards.</InfoPop>}>
          <button className="btn btn-danger" disabled={!!busy} onClick={() => run('tamper')}><Bomb size={15} />{busy === 'tamper' ? 'Simulating…' : 'Run tamper simulation'}</button>
          {tamper && (
            <div style={{ marginTop: 12 }}>
              <div className="secondary" style={{ fontSize: 13 }}>Changed one character in <b>post #{tamper.tampered_seq}</b> (on a copy).</div>
              <div className="row-wrap" style={{ marginTop: 8 }}>
                {tamper.verify_result?.status === 'FAIL'
                  ? <StatusBadge status="critical">Detected: {tamper.verify_result.reason}</StatusBadge>
                  : <StatusBadge status="warning">Not detected</StatusBadge>}
                {tamper.detected_at_expected_seq && <StatusBadge status="good">Pinpointed the exact post</StatusBadge>}
              </div>
            </div>
          )}
        </Card>
      </div>
      {err && <div className="notice crit" style={{ marginBottom: 16 }}>{err}</div>}

      <div className="grid g-2">
        <Card title="Signed seals" sub="newest first">
          <table className="tbl">
            <thead><tr><th>#</th><th>Posts</th><th>Fingerprint</th><th>Bitcoin</th></tr></thead>
            <tbody>{(cps?.checkpoints ?? []).map((c: any) => (
              <tr key={c.id}><td className="tnum">{c.id}</td><td className="tnum">{c.first_seq}–{c.last_seq}</td><td className="mono" style={{ fontSize: 12 }} title={c.merkle_root}>{short(c.merkle_root)}</td>
                <td>{c.ots_status ? <span className="chip">{c.ots_status}</span> : <span className="muted">—</span>}</td></tr>
            ))}</tbody>
          </table>
        </Card>
        <Card title="Proof of inclusion" sub="prove a single post is part of a signed seal">
          <div className="row">
            <input className="input" style={{ width: 140 }} inputMode="numeric" value={seq} onChange={e => setSeq(e.target.value.replace(/\D/g, ''))} aria-label="Record sequence number" />
            <button className="btn" disabled={!seq || !!busy} onClick={lookup}><SearchIcon size={14} />Get proof</button>
            <InfoPop>Anyone can check this proof with just the post, this short path and our public key.</InfoPop>
          </div>
          {proof && (
            <div style={{ marginTop: 12, fontSize: 13 }} className="stack">
              <div className="row"><KeyRound size={14} />Seal {proof.checkpoint.id} (posts {proof.checkpoint.first_seq}–{proof.checkpoint.last_seq})</div>
              <div className="mono" style={{ fontSize: 12 }}>entry {short(proof.record.entry_hash)}</div>
              <ol style={{ margin: 0, paddingLeft: 18 }} className="mono">
                {proof.path.map((p: any, i: number) => <li key={i} style={{ fontSize: 12 }}>{p.position === 'left' ? 'left ' : 'right'} {short(p.hash)}</li>)}
              </ol>
              <div className="mono" style={{ fontSize: 12 }}>root {short(proof.checkpoint.merkle_root)} · signed by {proof.checkpoint.pubkey_id}</div>
            </div>
          )}
        </Card>
      </div>

      <Card title="Activity log" sub="every analyst action is sealed too" style={{ marginTop: 20 }}>
        {(audit?.entries ?? []).length === 0 ? <div className="muted">No actions yet.</div> : (
          <table className="tbl">
            <thead><tr><th>Time</th><th>Action</th><th className="num">Evidence #</th></tr></thead>
            <tbody>{audit.entries.slice(0, 10).map((a: any) => (
              <tr key={a.id}><td>{ist(a.ts)}</td><td style={{ textTransform: 'capitalize' }}>{a.action.replace(/_/g, ' ')}</td><td className="num">{a.ledger_seq}</td></tr>
            ))}</tbody>
          </table>
        )}
      </Card>
      <NextStep />
    </div>
  )
}
