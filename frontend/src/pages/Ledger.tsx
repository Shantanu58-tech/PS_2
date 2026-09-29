import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Bomb, KeyRound, Search as SearchIcon, ShieldCheck } from 'lucide-react'
import { getJSON, postJSON, useAudit, useCheckpoints, useLedgerStatus } from '../hooks/useApi'
import { Card, InfoPop, Kpi, PageHead, StatusBadge } from '../components/ui'
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
      <PageHead code="THEME" title="Evidence ledger"
        sub="Append-only and tamper-evident: every record is hashed (SHA-256) and chained to the previous entry. Every 100 entries a Merkle root is signed with Ed25519, and roots can be anchored to Bitcoin through OpenTimestamps." />
      <div className="grid g-4" style={{ marginBottom: 16 }}>
        <Kpi label="Records" value={num(status?.record_count)} foot={`last seq ${num(status?.last_seq)}`} />
        <Kpi label="Signed checkpoints" value={num(status?.checkpoint_count)} foot="Merkle root + Ed25519 per 100 records" />
        <Kpi label="Signing key" value={<span className="mono" style={{ fontSize: 18 }}>{status?.pubkey_id ?? '—'}</span>} foot="public-key fingerprint" />
        <Kpi label="Bitcoin anchoring" value={status?.last_checkpoint?.ots_status ?? (status?.ots_enabled ? 'enabled' : 'off')} foot="OpenTimestamps"
          info={<>The newest checkpoint root is stamped on public OpenTimestamps calendars and later upgraded to a Bitcoin block attestation. Because entries are chained, one anchor covers every earlier record.</>} />
      </div>

      <div className="grid g-2" style={{ marginBottom: 16 }}>
        <Card title="Verify integrity" sub="recompute every record hash, chain link, Merkle root and signature">
          <button className="btn btn-primary" disabled={!!busy} onClick={() => run('verify')}><ShieldCheck size={15} />{busy === 'verify' ? 'Verifying…' : 'Verify integrity'}</button>
          {verify && (
            <div style={{ marginTop: 12 }}>
              {verify.status === 'PASS'
                ? <StatusBadge status="good">VERIFICATION PASSED</StatusBadge>
                : <StatusBadge status="critical">VERIFICATION FAILED</StatusBadge>}
              <div className="secondary" style={{ marginTop: 8, fontSize: 13 }}>
                {num(verify.records)} records and {num(verify.checkpoints)} signed checkpoints checked in {verify.seconds}s.
                {verify.status !== 'PASS' && <> First failure at seq {verify.seq}: {verify.reason}.</>}
              </div>
            </div>
          )}
        </Card>
        <Card title="Tamper simulation" sub="change one character of one stored record, on a scratch copy only"
          actions={<InfoPop>The real ledger is never modified: the database is copied to a temporary file, the append-only trigger is dropped on the copy, one record's payload is changed, and the copy is verified and deleted.</InfoPop>}>
          <button className="btn btn-danger" disabled={!!busy} onClick={() => run('tamper')}><Bomb size={15} />{busy === 'tamper' ? 'Simulating…' : 'Run tamper simulation'}</button>
          {tamper && (
            <div style={{ marginTop: 12 }}>
              <div className="secondary" style={{ fontSize: 13 }}>Mutated record <b className="mono">seq {tamper.tampered_seq}</b> at byte {tamper.byte_offset} (scratch copy).</div>
              <div className="row-wrap" style={{ marginTop: 8 }}>
                {tamper.verify_result?.status === 'FAIL'
                  ? <StatusBadge status="critical">Detected: {tamper.verify_result.reason}</StatusBadge>
                  : <StatusBadge status="warning">Not detected</StatusBadge>}
                {tamper.detected_at_expected_seq && <StatusBadge status="good">Pinpointed exact record</StatusBadge>}
              </div>
              <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>The original ledger is unchanged. Run Verify again to confirm.</div>
            </div>
          )}
        </Card>
      </div>
      {err && <div className="notice crit" style={{ marginBottom: 16 }}>{err}</div>}

      <div className="grid g-2">
        <Card title="Signed checkpoints" sub="newest first">
          <table className="tbl">
            <thead><tr><th>#</th><th>Seq range</th><th>Merkle root</th><th>OTS</th></tr></thead>
            <tbody>{(cps?.checkpoints ?? []).map((c: any) => (
              <tr key={c.id}><td className="tnum">{c.id}</td><td className="tnum">{c.first_seq}–{c.last_seq}</td><td className="mono" style={{ fontSize: 12 }} title={c.merkle_root}>{short(c.merkle_root)}</td>
                <td>{c.ots_status ? <span className="chip">{c.ots_status}</span> : <span className="muted">—</span>}</td></tr>
            ))}</tbody>
          </table>
        </Card>
        <Card title="Inclusion proof" sub="prove one record belongs to a signed checkpoint">
          <div className="row">
            <input className="input" style={{ width: 140 }} inputMode="numeric" value={seq} onChange={e => setSeq(e.target.value.replace(/\D/g, ''))} aria-label="Record sequence number" />
            <button className="btn" disabled={!seq || !!busy} onClick={lookup}><SearchIcon size={14} />Get proof</button>
            <InfoPop>A verifier needs only the record, this Merkle path and the ledger public key. Hash the entry up the path and compare with the signed root.</InfoPop>
          </div>
          {proof && (
            <div style={{ marginTop: 12, fontSize: 13 }} className="stack">
              <div className="row"><KeyRound size={14} />Checkpoint {proof.checkpoint.id} (seq {proof.checkpoint.first_seq}–{proof.checkpoint.last_seq}) · leaf index {proof.index}</div>
              <div className="mono" style={{ fontSize: 12 }}>entry {short(proof.record.entry_hash)}</div>
              <ol style={{ margin: 0, paddingLeft: 18 }} className="mono">
                {proof.path.map((p: any, i: number) => <li key={i} style={{ fontSize: 12 }}>{p.position === 'left' ? 'left ' : 'right'} {short(p.hash)}</li>)}
              </ol>
              <div className="mono" style={{ fontSize: 12 }}>root {short(proof.checkpoint.merkle_root)} · signed by {proof.checkpoint.pubkey_id}</div>
            </div>
          )}
        </Card>
      </div>

      <Card title="Audit trail" sub="analyst actions are written into the same hash chain" style={{ marginTop: 16 }}>
        {(audit?.entries ?? []).length === 0 ? <div className="muted">No analyst actions yet.</div> : (
          <table className="tbl">
            <thead><tr><th>Time</th><th>Action</th><th>Detail</th><th className="num">Ledger seq</th></tr></thead>
            <tbody>{audit.entries.map((a: any) => (
              <tr key={a.id}><td>{ist(a.ts)}</td><td>{a.action.replace(/_/g, ' ')}</td><td className="mono" style={{ fontSize: 12 }}>{a.detail_json}</td><td className="num mono">{a.ledger_seq}</td></tr>
            ))}</tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
