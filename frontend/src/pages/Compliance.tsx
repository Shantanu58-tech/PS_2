import { Link } from 'react-router-dom'
import { ExternalLink } from 'lucide-react'
import { useEvalSummary, useTraceability } from '../hooks/useApi'
import { Card, InfoPop, Kpi, PageHead, StatusBadge } from '../components/ui'
import { ist, num, pct } from '../lib/fmt'

const NM = 'not yet measured'

function fmtMetric(v: any): string {
  if (v === null || v === undefined || v === NM) return NM
  if (typeof v === 'number') return Math.abs(v) <= 1 && !Number.isInteger(v) ? v.toFixed(3) : num(v, 2)
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

export default function Compliance() {
  const { data: tr } = useTraceability()
  const { data: ev } = useEvalSummary()
  const rows: any[] = tr?.requirements ?? []
  const measured = ev && !ev.status
  const c = ev?.coordination ?? {}, b = ev?.burst ?? {}, e = ev?.emotion ?? {}, p = ev?.phash ?? {}, l = ev?.ledger ?? {}, d = ev?.demographics ?? {}, g = ev?.graph ?? {}, li = ev?.lineage ?? {}

  return (
    <div>
      <PageHead code="PS 26152" title="Problem statement coverage & evaluation"
        sub={<>Every requirement mapped to the module, test and page that implement it. Every number here is read from <span className="mono">eval/reports/summary.json</span> (produced by <span className="mono">make eval</span>) and is never typed in by hand.</>} />
      <div className="notice" style={{ marginBottom: 16 }}>
        Evaluation uses a fully synthetic 7-day scenario with ground truth. Detector weights and emotion thresholds were tuned on seed 7; headline numbers come from held-out seed 11.
        {ev?.generated_at && <span className="muted"> Generated {ist(ev.generated_at)}.</span>}
      </div>

      <Card title="Requirement traceability" style={{ marginBottom: 16 }}>
        <div className="table-wrap">
          <table className="tbl">
            <thead><tr><th>PS</th><th>Requirement</th><th>What we built</th><th>Measured</th><th>Status</th><th /></tr></thead>
            <tbody>{rows.map(r => (
              <tr key={r.ps}>
                <td className="mono" style={{ fontWeight: 700 }}>{r.ps}</td>
                <td style={{ minWidth: 160 }}>{r.requirement}</td>
                <td className="secondary" style={{ fontSize: 12.5, minWidth: 240 }}>{r.component}</td>
                <td className="mono" style={{ fontSize: 12 }}>{r.metric_name}<div style={{ color: 'var(--ink-1)' }}>{fmtMetric(r.metric_value)}</div></td>
                <td>{r.status === 'built' ? <StatusBadge status="good">Built</StatusBadge> : <StatusBadge status="warning">Partial</StatusBadge>}</td>
                <td><Link className="btn btn-sm btn-ghost" to={r.page}>View</Link></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>

      {measured && (
        <>
          <h2 className="card-title" style={{ fontSize: 15, margin: '4px 0 12px' }}>Scoreboard</h2>
          <div className="grid g-4" style={{ marginBottom: 16 }}>
            <Kpi label="Coordination F1 (held-out)" value={c.f1?.toFixed(2) ?? NM} foot={`P ${c.precision?.toFixed(2)} · R ${c.recall?.toFixed(2)} · baselines ${c.baseline_age_ratio_f1?.toFixed(2)} / ${c.baseline_exact_duplicate_f1?.toFixed(2)}`}
              info={<>Account-level, against the planted ground truth. False positives on held-out seed 11: {c.decoy_accounts_flagged} fan-club accounts (a legitimate synchronized group). Validation seed F1 {c.validation_f1?.toFixed(2)}.</>} />
            <Kpi label="Rumour lead time" value={b.lead_time_minutes != null ? `${b.lead_time_minutes} min` : NM} foot="ahead of a keyword-volume alarm"
              info={<>Online test: Kleinberg re-run on growing prefixes (5-minute steps) vs a naive hourly keyword z &gt; 3 alarm.</>} />
            <Kpi label="High-priority alerts / day" value={b.high_priority_alerts_per_day ?? NM} foot={`vs ${b.naive_alerts_per_day} naive · decoy high-priority: ${b.decoy_high_priority_alerts}`} />
            <Kpi label="Tamper detection" value={l.tamper_detection_rate != null ? pct(l.tamper_detection_rate, 0) : NM} foot={`${num(l.tamper_trials)} trials · verify 100k records in ${l.verify_100k_seconds}s`} />
            <Kpi label="pHash image matching" value={p.recall_at_chosen != null ? pct(p.recall_at_chosen, 1) : NM} foot={`recall at FPR ${pct(p.fpr_at_chosen, 1)} (T = ${p.chosen_threshold})`} />
            <Kpi label="Lineage" value={li.earliest_platform ?? NM} foot={`origin found: ${li.origin_found ? 'yes' : 'no'} · to X in ${li.telegram_to_x_minutes} min · variants ${li.image_variants_linked}`} />
            <Kpi label="Emotion macro-F1" value={e.macro_f1?.toFixed(2) ?? NM} foot={`synthetic labels · zero-shot baseline ${e.baseline_zero_shot_nli_macro_f1?.toFixed(2)}`}
              info={<>Measured against synthetic template labels, not a human gold set ({e.gold_set}). Sarcasm is weak. The raw-vs-organic panic distortion is currently inverted (×{e.distortion?.distortion_ratio}), so it is not claimed.</>} />
            <Kpi label="Geography accuracy" value={d.geo_accuracy != null ? pct(d.geo_accuracy, 0) : NM} foot={`coverage ${pct(d.geo_coverage, 0)} · buckets below k: ${d.released_buckets_below_k}`} />
          </div>
          <div className="grid g-2">
            <Card title="Network" sub="planted bridge account">
              <div style={{ fontSize: 24, fontWeight: 650 }}>rank #{g.bridge_rank ?? '—'}</div>
              <div className="muted" style={{ fontSize: 12 }}>{num(g.nodes)} accounts · {num(g.edges)} interaction edges</div>
            </Card>
            <Card title="Detailed reports" actions={<InfoPop>Markdown reports written by the evaluation harness.</InfoPop>}>
              <div className="row-wrap">
                {['coordination', 'alerts', 'emotion', 'phash', 'ledger', 'components'].map(r => (
                  <a key={r} className="btn btn-sm" href={`/api/eval/reports/${r}`} target="_blank" rel="noreferrer"><ExternalLink size={13} />{r}</a>
                ))}
              </div>
            </Card>
          </div>
        </>
      )}

      <Card title="Limitations we state openly" style={{ marginTop: 16 }}>
        <ul style={{ margin: 0, paddingLeft: 18, color: 'var(--ink-2)', fontSize: 13, lineHeight: 1.7 }}>
          <li>Demo data is synthetic. Collectors are live-capable but need platform credentials.</li>
          <li>Emotion is the weakest component: synthetic labels, no gold set, weak sarcasm, and the model keys on emotion words.</li>
          <li>Coordination flags a legitimate fan swarm on the held-out seed; the score is a signal for review, not an accusation.</li>
          <li>Lineage reports the earliest <i>observed</i> origin, not necessarily the true origin.</li>
          <li>Age inference is coarse (bio cues only) and covers few accounts.</li>
          <li>The §63 certificate is a draft for counsel; no admissibility is claimed.</li>
        </ul>
      </Card>
    </div>
  )
}
