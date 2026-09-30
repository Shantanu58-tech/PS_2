"""Case briefs and draft Section 63 (BSA 2023) certificates.

A case is opened from an alert. The brief assembles: alert + topic, evidence
posts with their ledger sequence numbers and record hashes, the signed
Merkle checkpoints covering them, cross-platform lineage, raw vs organic
affect, coordination statistics and (if available) the LLM summary.
The certificate is a DRAFT for counsel review - never presented as legally
sufficient.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, select_autoescape

from app.config import settings
from app.version import VERSION

_env = Environment(autoescape=select_autoescape(default=True))

BRIEF_TEMPLATE = _env.from_string("""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Case {{ case_id }} brief</title>
<style>
 body{font-family:Inter,Segoe UI,Arial,sans-serif;margin:32px;color:#111;max-width:1000px}
 .banner{background:#7f1d1d;color:#fff;padding:8px 14px;font-weight:600;border-radius:6px}
 h1{margin:16px 0 4px} .muted{color:#555;font-size:13px}
 .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0}
 .kpi{border:1px solid #ddd;border-radius:8px;padding:10px}.kpi b{font-size:20px;display:block}
 table{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0}
 th,td{border:1px solid #ddd;padding:6px;text-align:left;vertical-align:top} th{background:#f3f4f6}
 code{font-size:11px;word-break:break-all} section{margin:22px 0}
</style></head><body>
{% if synthetic %}<div class="banner">SIMULATED SCENARIO - no real persons or events</div>{% endif %}
<h1>Case {{ case_id }}: {{ title }}</h1>
<div class="muted">Generated {{ generated_at }} UTC - DEEPASTAMBHA v{{ version }} - mode {{ mode }}</div>
<div class="grid">
 <div class="kpi">Priority<b>{{ "%.0f"|format(alert.priority) }}/100</b></div>
 <div class="kpi">Coordinated share<b>{{ "%.0f"|format(100 * ev.get('coordinated_share', 0)) }}%</b></div>
 <div class="kpi">Posts in burst<b>{{ ev.get('n_posts', '-') }}</b></div>
 <div class="kpi">Burst level<b>{{ ev.get('burst_level', '-') }}</b></div>
</div>
<section><h2>Alert</h2><p><b>{{ alert.headline }}</b></p>
 <p class="muted">Window {{ ev.get('start', '') }} to {{ ev.get('end', '') }} - platforms {{ ev.get('platforms', [])|join(', ') }}</p></section>
{% if summary %}<section><h2>Narrative summary (LLM-assisted, verify against evidence)</h2>
 <p>{{ summary.summary }}</p><ul>{% for c in summary.key_claims %}<li>{{ c }}</li>{% endfor %}</ul></section>{% endif %}
<section><h2>Lineage (earliest observed)</h2>
 <table><tr><th>Platform</th><th>First seen (UTC)</th><th>First post</th><th>Posts</th></tr>
 {% for p in lineage.platforms %}<tr><td>{{ p.platform }}</td><td>{{ p.first_seen }}</td><td>{{ p.text }}</td><td>{{ p.n_posts }}</td></tr>{% endfor %}
 </table><p class="muted">{{ lineage.caveat }}</p></section>
<section><h2>Affect: raw vs organic-only</h2>
 <table><tr><th></th>{% for k in dims %}<th>{{ k }}</th>{% endfor %}<th>posts</th></tr>
 {% for label, row in affect.items() %}<tr><td>{{ label }}</td>{% for k in dims %}<td>{{ "%.2f"|format(row[k] or 0) }}</td>{% endfor %}<td>{{ row.n }}</td></tr>{% endfor %}
 </table></section>
{% if cluster %}<section><h2>Coordination</h2>
 <p>Cluster #{{ cluster.cluster_id }} - score {{ "%.2f"|format(cluster.score) }}, {{ cluster.n_accounts }} accounts,
 normalised entropy {{ "%.2f"|format(cluster.hn) }}, synchrony {{ "%.2f"|format(cluster.sync) }},
 cross-account duplicate ratio {{ "%.2f"|format(cluster.dup_ratio) }}.
 Statistical signal for review, not an accusation.</p></section>{% endif %}
<section><h2>Evidence index</h2>
 <table><tr><th>Ledger seq</th><th>Platform</th><th>Created (UTC)</th><th>Text</th><th>Record hash</th></tr>
 {% for e in evidence %}<tr><td>{{ e.ledger_seq }}</td><td>{{ e.platform }}</td><td>{{ e.created_at }}</td><td>{{ e.text }}</td><td><code>{{ e.record_hash }}</code></td></tr>{% endfor %}
 </table></section>
<section><h2>Integrity</h2>
 <table><tr><th>Checkpoint</th><th>Seq range</th><th>Merkle root</th><th>Ed25519 key</th><th>OTS</th></tr>
 {% for c in checkpoints %}<tr><td>{{ c.id }}</td><td>{{ c.first_seq }}-{{ c.last_seq }}</td><td><code>{{ c.merkle_root }}</code></td><td>{{ c.pubkey_id }}</td><td>{{ c.ots_status or 'not anchored' }}</td></tr>{% endfor %}
 </table><p class="muted">Ledger verification at generation time: {{ verify_status }}. Re-verify: POST /api/ledger/verify</p></section>
</body></html>""")

CERT_TEMPLATE = _env.from_string("""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Section 63 draft certificate - case {{ case_id }}</title>
<style>body{font-family:'Times New Roman',serif;margin:56px;max-width:820px}
.draft{background:#b91c1c;color:#fff;padding:12px;text-align:center;font-weight:bold}
.sig{border-top:1px solid #000;width:300px;margin-top:48px} code{word-break:break-all}</style></head><body>
<div class="draft">DRAFT FOR REVIEW AND SIGNATURE - NOT A LEGAL OPINION - REQUIRES COUNSEL REVIEW BEFORE ANY USE</div>
<h2 style="text-align:center">Certificate under Section 63 of the Bharatiya Sakshya Adhiniyam, 2023</h2>
<p><b>Case:</b> {{ case_id }} - {{ title }}<br><b>Generated:</b> {{ generated_at }} UTC</p>
<h3>1. Description of the electronic records</h3>
<p>{{ n_records }} records collected by DEEPASTAMBHA v{{ version }} ({{ mode }} mode), ledger sequence numbers
{{ first_seq }} to {{ last_seq }}. {% if synthetic %}<b>These records are SIMULATED test data.</b>{% endif %}</p>
<h3>2. Manner of production</h3>
<p>Records were collected through automated connectors, canonicalised (sorted-key JSON) and appended to an
append-only SQLite ledger enforced by database triggers. Each entry stores SHA-256(payload) and an entry hash
chaining the previous entry. Batches of 100 entries are summarised by a Merkle root signed with Ed25519
(key fingerprint {{ pubkey_id }}).</p>
<h3>3. Integrity particulars</h3>
<ul>{% for c in checkpoints %}<li>Checkpoint {{ c.id }} (seq {{ c.first_seq }}-{{ c.last_seq }}): Merkle root <code>{{ c.merkle_root }}</code>{% if c.ots_status %}; OpenTimestamps: {{ c.ots_status }}{% endif %}</li>{% endfor %}</ul>
<p>Full-chain verification result at generation: <b>{{ verify_status }}</b>.</p>
<h3>4. Statement</h3>
<p>[To be completed by the responsible person: operation of the computer during the relevant period,
absence of malfunction affecting accuracy, and the person's responsible position.]</p>
<div class="sig"></div><p>Signature of responsible person - Name / Designation / Date</p>
<div class="sig"></div><p>Signature of expert - Name / Designation / Date</p>
<p style="font-size:12px;color:#555">Generated by software as a drafting aid. No claim of admissibility is made.</p>
</body></html>""")

DIMS = ["anxiety", "excitement", "supportive", "against", "sarcasm"]


def _cases_dir() -> Path:
    d = Path(settings.data_dir) / "cases"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _gather(conn: sqlite3.Connection, case_id: int) -> dict:
    from app.analytics.lineage import topic_lineage
    from app.ledger.verify import verify_chain

    case = conn.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
    if not case:
        raise ValueError(f"Case {case_id} not found")
    alert = conn.execute("SELECT * FROM alerts WHERE alert_id=?", (case["alert_id"],)).fetchone()
    alert_d = dict(alert) if alert else {"priority": 0.0, "headline": case["title"], "evidence_json": "{}"}
    ev = json.loads(alert_d.get("evidence_json") or "{}")
    topic_id = ev.get("topic_id") or alert_d.get("topic_id")
    evidence: list[dict] = []
    if topic_id is not None:
        evidence = [dict(r) for r in conn.execute(
            "SELECT p.platform, p.post_id, p.text, p.created_at, p.ledger_seq, r.record_hash "
            "FROM topic_assign ta JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id "
            "LEFT JOIN raw_records r ON r.seq=p.ledger_seq WHERE ta.topic_id=? "
            "AND p.created_at >= COALESCE(?, '') AND p.created_at <= COALESCE(?, '9999') "
            "ORDER BY p.created_at LIMIT 50",
            (topic_id, ev.get("start"), ev.get("end")),
        )]
    seqs = [e["ledger_seq"] for e in evidence if e["ledger_seq"]]
    checkpoints = [dict(r) for r in conn.execute(
        "SELECT id, first_seq, last_seq, merkle_root, pubkey_id, ots_status FROM ledger_checkpoints "
        "WHERE last_seq >= ? AND first_seq <= ? ORDER BY id",
        (min(seqs, default=0), max(seqs, default=-1)),
    )]
    affect = {}
    for label, extra in (("raw", ""), ("organic only", "AND NOT EXISTS (SELECT 1 FROM coord_accounts ca "
                         "WHERE ca.platform=p.platform AND ca.account_id=p.author_id AND ca.score >= 0.7)")):
        row = conn.execute(
            f"SELECT AVG(pe.anxiety) anxiety, AVG(pe.excitement) excitement, AVG(pe.supportive) supportive, "
            f"AVG(pe.against) against, AVG(pe.sarcasm) sarcasm, COUNT(*) n FROM topic_assign ta "
            f"JOIN posts p ON p.platform=ta.platform AND p.post_id=ta.post_id "
            f"JOIN post_emotions pe ON pe.platform=p.platform AND pe.post_id=p.post_id "
            f"WHERE ta.topic_id=? {extra}", (topic_id,),
        ).fetchone()
        affect[label] = dict(row)
    cluster = conn.execute("SELECT * FROM coord_clusters WHERE topic_id=? ORDER BY score DESC LIMIT 1",
                           (topic_id,)).fetchone()
    summary_row = conn.execute("SELECT summary FROM summaries WHERE scope='topic' AND scope_id=?",
                               (str(topic_id),)).fetchone()
    synthetic = bool(conn.execute(
        "SELECT MIN(synthetic) FROM posts p JOIN topic_assign ta ON ta.platform=p.platform "
        "AND ta.post_id=p.post_id WHERE ta.topic_id=?", (topic_id,)).fetchone()[0])
    return {
        "case": dict(case), "alert": alert_d, "ev": ev, "topic_id": topic_id, "evidence": evidence,
        "checkpoints": checkpoints, "affect": affect, "cluster": dict(cluster) if cluster else None,
        "summary": json.loads(summary_row[0]) if summary_row else None,
        "lineage": topic_lineage(conn_path(conn), topic_id) if topic_id is not None else
        {"platforms": [], "caveat": ""},
        "verify": verify_chain(conn_path(conn)),
        "synthetic": synthetic or settings.mode == "replay",
    }


def conn_path(conn: sqlite3.Connection) -> str:
    return conn.execute("PRAGMA database_list").fetchone()[2]


def generate_brief(db_path: str, case_id: int, output_dir: str | None = None) -> str:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        g = _gather(conn, case_id)
    html = BRIEF_TEMPLATE.render(
        case_id=case_id, title=g["case"]["title"], generated_at=datetime.now(timezone.utc).isoformat(),
        version=VERSION, mode=settings.mode.upper(), synthetic=g["synthetic"], alert=g["alert"], ev=g["ev"],
        summary=g["summary"], lineage=g["lineage"], affect=g["affect"], dims=DIMS, cluster=g["cluster"],
        evidence=g["evidence"], checkpoints=g["checkpoints"], verify_status=g["verify"].get("status"),
    )
    out = Path(output_dir) if output_dir else _cases_dir()
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"case_{case_id}_brief.html"
    path.write_text(html, encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE cases SET brief_path=? WHERE case_id=?", (str(path), case_id))
        conn.commit()
    return str(path)


def generate_certificate(db_path: str, case_id: int, output_dir: str | None = None) -> str:
    from app.ledger.sign import Signer

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        g = _gather(conn, case_id)
    seqs = [e["ledger_seq"] for e in g["evidence"] if e["ledger_seq"]]
    first_seq, last_seq = min(seqs, default=0), max(seqs, default=0)
    html = CERT_TEMPLATE.render(
        case_id=case_id, title=g["case"]["title"], generated_at=datetime.now(timezone.utc).isoformat(),
        version=VERSION, mode=settings.mode, synthetic=g["synthetic"], n_records=len(seqs),
        first_seq=first_seq, last_seq=last_seq, checkpoints=g["checkpoints"],
        pubkey_id=Signer().pubkey_id, verify_status=g["verify"].get("status"),
    )
    out = Path(output_dir) if output_dir else _cases_dir()
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"case_{case_id}_cert_draft.html"
    path.write_text(html, encoding="utf-8")
    root = g["checkpoints"][-1]["merkle_root"] if g["checkpoints"] else "N/A"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO certificates (case_id, generated_at, pdf_path, first_seq, last_seq, merkle_root) "
            "VALUES (?,?,?,?,?,?)",
            (case_id, datetime.now(timezone.utc).isoformat(), str(path), first_seq, last_seq, root),
        )
        conn.commit()
    return str(path)
