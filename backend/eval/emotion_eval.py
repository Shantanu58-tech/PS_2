"""Emotion scoring on the scenario's synthetic template labels.

IMPORTANT: these are labels attached to generated templates, not a human-
audited gold set (PRD 11.1 requires 400 audited items + Cohen's kappa; that
is a human task). Reported separately as 'synthetic-label agreement'.
Also measures the raw vs organic-only distortion in the rumour window.
"""
from __future__ import annotations

from eval.common import connect, md_table, prf, write_report

LABELS = {"anxiety": "anxious_post_ids", "sarcasm": "sarcasm_post_ids", "excitement": "excitement_post_ids"}
THRESH = 0.5  # fallback when no tuned threshold exists


def _thresh(label: str) -> float:
    from app.nlp.emotion import thresholds

    return thresholds().get(label, THRESH)


def _scores(db: str, ids: set[str], table: str = "post_emotions") -> dict[str, dict]:
    with connect(db) as c:
        rows = c.execute(
            f"SELECT p.post_id, p.text, p.lang, e.* FROM {table} e JOIN posts p "
            "ON p.platform=e.platform AND p.post_id=e.post_id").fetchall()
    return {r["post_id"]: dict(r) for r in rows if r["post_id"] in ids}


def _lexicon_scores(texts: dict[str, str]) -> dict[str, dict]:
    from app.nlp.emotion import lexicon_scores

    return {pid: lexicon_scores(t) for pid, t in texts.items()}


HYPOTHESES = {
    "anxiety": "This message expresses or spreads fear, panic or alarm.",
    "sarcasm": "The author is being sarcastic or mocking.",
    "excitement": "The author is excited or celebrating.",
}


def _zero_shot_scores(texts: dict[str, str]) -> dict[str, dict] | None:
    """PRD 8.B baseline (c): zero-shot multilingual NLI (mDeBERTa-v3 XNLI),
    multi-label, one entailment score per dimension."""
    try:
        from transformers import pipeline

        from app.nlp.models import MODELS, local_dir

        if not (local_dir(MODELS["nli"]) / "config.json").exists():
            return None
        clf = pipeline("zero-shot-classification", model=str(local_dir(MODELS["nli"])), device=-1)
    except Exception:
        return None
    uniq = list(dict.fromkeys(texts.values()))
    labels = list(HYPOTHESES)
    by_text = {}
    for t in uniq:
        out = clf(t, candidate_labels=[HYPOTHESES[k] for k in labels], multi_label=True,
                  hypothesis_template="{}")
        score = dict(zip(out["labels"], out["scores"]))
        by_text[t] = {k: float(score[HYPOTHESES[k]]) for k in labels}
    return {pid: by_text[t] for pid, t in texts.items()}


def _eval_label(scored: dict[str, dict], positives: set[str], label: str, t: float = THRESH) -> dict:
    tp = sum(1 for pid, s in scored.items() if pid in positives and s[label] >= t)
    fp = sum(1 for pid, s in scored.items() if pid not in positives and s[label] >= t)
    fn = sum(1 for pid, s in scored.items() if pid in positives and s[label] < t)
    return prf(tp, fp, fn)


def distortion(db: str, truth: dict) -> dict:
    """Anxiety share (posts with anxiety >= 0.5) in the rumour window, raw vs organic-only."""
    from datetime import datetime, timedelta

    t0 = datetime.fromisoformat(truth["t0"])
    start, end = t0.isoformat(), (t0 + timedelta(hours=3)).isoformat()
    q = (f"SELECT AVG(CASE WHEN e.anxiety >= {_thresh('anxiety')} THEN 1.0 ELSE 0.0 END), COUNT(*) FROM post_emotions e "
         "JOIN posts p ON p.platform=e.platform AND p.post_id=e.post_id WHERE p.created_at BETWEEN ? AND ? "
         "AND lower(p.text) LIKE '%dam%' {extra}")
    organic = ("AND NOT EXISTS (SELECT 1 FROM coord_accounts ca WHERE ca.platform=p.platform "
               "AND ca.account_id=p.author_id AND ca.score >= 0.7)")
    with connect(db) as c:
        raw = c.execute(q.format(extra=""), (start, end)).fetchone()
        org = c.execute(q.format(extra=organic), (start, end)).fetchone()
    raw_share, org_share = raw[0] or 0.0, org[0] or 0.0
    return {"window": f"{start} + 3h (posts mentioning the dam)",
            "raw_anxiety_share": round(raw_share, 4), "raw_posts": raw[1],
            "organic_anxiety_share": round(org_share, 4), "organic_posts": org[1],
            "distortion_ratio": round(raw_share / org_share, 2) if org_share else None}


def evaluate(built: dict, heldout: dict | None = None) -> dict:
    """Headline on the held-out seed (thresholds tuned on the validation seed)."""
    target = heldout or built
    db, truth = target["db"], target["truth"]
    positives = {k: set(truth["labels"][v]) for k, v in LABELS.items()}
    pool = set().union(*positives.values())
    scored = _scores(db, pool)
    with connect(db) as c:
        texts = {r[0]: r[1] for r in c.execute("SELECT post_id, text FROM posts") if r[0] in pool}
    lex = _lexicon_scores(texts)
    zs = _zero_shot_scores(texts)
    rows, macro, macro_lex, macro_zs = [], [], [], []
    for label, pos in positives.items():
        ours = _eval_label(scored, pos, label, _thresh(label))
        base = _eval_label(lex, pos, label)
        macro.append(ours["f1"])
        macro_lex.append(base["f1"])
        rows.append({"label": label, "model": "pre-trained pipeline (ours)", **ours})
        if zs is not None:
            z = _eval_label(zs, pos, label)
            macro_zs.append(z["f1"])
            rows.append({"label": label, "model": "zero-shot mDeBERTa NLI (baseline c)", **z})
        rows.append({"label": label, "model": "lexicon (LEAKY: written with the templates)", **base})
    hinglish = {pid for pid, s in scored.items() if s.get("lang") == "hi-Latn"}
    hing_f1 = []
    for label, pos in positives.items():
        sub = {pid: s for pid, s in scored.items() if pid in hinglish}
        if sub:
            hing_f1.append(_eval_label(sub, pos & hinglish, label, _thresh(label))["f1"])
    model_versions = sorted({s["model_version"] for s in scored.values()})
    dist = distortion(db, truth)
    out = {
        "evaluated_seed": truth["scenario_seed"],
        "thresholds": {k: _thresh(k) for k in LABELS},
        "label_source": "synthetic scenario template labels (NOT a human-audited gold set)",
        "macro_f1": round(sum(macro) / len(macro), 4),
        "baseline_lexicon_macro_f1": round(sum(macro_lex) / len(macro_lex), 4),
        "baseline_lexicon_is_leaky": True,
        "baseline_zero_shot_nli_macro_f1": round(sum(macro_zs) / len(macro_zs), 4) if macro_zs else None,
        "hinglish_subset_macro_f1": round(sum(hing_f1) / len(hing_f1), 4) if hing_f1 else None,
        "hinglish_subset_posts": len(hinglish), "n_labelled_posts": len(scored),
        "model_versions": model_versions, "per_label": rows, "gold_set": "not yet measured",
    }
    lines = [
        "**Label source:** synthetic scenario template labels, not a human-audited gold set. "
        "Gold-set macro-F1 (PRD 11.1): not yet measured.", "",
        f"Evaluated on seed {truth['scenario_seed']} (held-out); per-label thresholds tuned on the "
        f"validation seed: {out['thresholds']}. Models: {', '.join(model_versions)}. "
        "Baselines use threshold 0.5.", "",
        *md_table(rows, ["label", "model", "precision", "recall", "f1", "tp", "fp", "fn"]),
        "", f"Macro-F1: pre-trained pipeline {out['macro_f1']}; zero-shot NLI baseline "
        f"{out['baseline_zero_shot_nli_macro_f1']}; lexicon {out['baseline_lexicon_macro_f1']}. "
        f"Hinglish subset macro-F1 (pipeline) {out['hinglish_subset_macro_f1']} (n={len(hinglish)}).", "",
        "**Caveat:** the lexicon was written by the same team that wrote the scenario templates, so it "
        "leaks the labels and is an upper bound, not a fair baseline. The fair comparison is the pipeline "
        "vs the zero-shot NLI baseline. Pre-trained models key on emotion words rather than meaning (a debunk "
        "saying 'stop spreading panic' scores higher anxiety than the rumour broadcast) and sarcasm stays weak; "
        "this motivates the PRD 11 MuRIL fine-tune.", "",
        "## Raw vs organic-only distortion (rumour window)", "",
        *md_table([dist], ["raw_anxiety_share", "organic_anxiety_share", "distortion_ratio", "raw_posts", "organic_posts"]),
    ]
    write_report("emotion", "Emotion inference evaluation", lines)
    return {**out, "distortion": dist}
