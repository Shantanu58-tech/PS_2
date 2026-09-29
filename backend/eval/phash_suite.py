"""pHash transformation suite (PRD 10.3): 200 generated base images (text-on-
gradient memes, deterministic), each transformed (resize 50-150%, JPEG
q10-90, crop 5-20%, watermark, blur, screenshot re-encode) = positive pairs,
plus 2,000 unrelated pairs. ROC over the Hamming threshold."""
from __future__ import annotations

import io
import random

import imagehash
from PIL import Image, ImageDraw, ImageFilter

from eval.common import md_table, write_report

WORDS = ["ALERT", "BREAKING", "SHARE", "FLOOD", "MATCH", "WIN", "RALLY", "PRICE", "EXAM", "RAIN", "NEWS", "VIRAL"]


def base_image(i: int) -> Image.Image:
    rng = random.Random(i)
    w, h = 320, 240
    c1 = [rng.randint(0, 255) for _ in range(3)]
    c2 = [rng.randint(0, 255) for _ in range(3)]
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(c1[k] * (1 - t) + c2[k] * t) for k in range(3)))
    for _ in range(rng.randint(3, 7)):
        x0, y0 = rng.randint(0, w - 40), rng.randint(0, h - 40)
        box = [x0, y0, x0 + rng.randint(20, 140), y0 + rng.randint(20, 120)]
        fill = tuple(rng.randint(0, 255) for _ in range(3))
        (d.ellipse if rng.random() < 0.5 else d.rectangle)(box, fill=fill)
    d.text((10, 10), " ".join(rng.sample(WORDS, 3)), fill=(255, 255, 255))
    return img


def transforms(img: Image.Image, rng: random.Random) -> list[tuple[str, Image.Image]]:
    w, h = img.size
    out = []
    s = rng.uniform(0.5, 1.5)
    out.append(("resize", img.resize((int(w * s), int(h * s)))))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=rng.randint(10, 90))
    out.append(("jpeg", Image.open(io.BytesIO(buf.getvalue())).convert("RGB")))
    c = rng.uniform(0.05, 0.20) / 2
    out.append(("crop", img.crop((int(w * c), int(h * c), int(w * (1 - c)), int(h * (1 - c)))).resize((w, h))))
    wm = img.copy()
    ImageDraw.Draw(wm).text((w - 110, h - 20), "@forwarded_by", fill=(255, 255, 255))
    out.append(("watermark", wm))
    out.append(("blur", img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.5, 2.0)))))
    # screenshot re-encode: pad with a UI frame, downscale, JPEG, crop back out
    frame = Image.new("RGB", (w + 40, h + 80), (30, 30, 30))
    frame.paste(img, (20, 50))
    frame = frame.resize(((w + 40) * 3 // 4, (h + 80) * 3 // 4))
    buf = io.BytesIO()
    frame.save(buf, "JPEG", quality=70)
    shot = Image.open(io.BytesIO(buf.getvalue())).convert("RGB")
    out.append(("screenshot", shot.crop((15, 37, 15 + w * 3 // 4, 37 + h * 3 // 4)).resize((w, h))))
    return out


def run(n_base: int = 200, n_negative: int = 2000, seed: int = 7) -> dict:
    rng = random.Random(seed)
    bases = [base_image(i) for i in range(n_base)]
    hashes = [imagehash.phash(b) for b in bases]
    pos: list[tuple[str, int]] = []
    for i, b in enumerate(bases):
        for name, t in transforms(b, rng):
            pos.append((name, hashes[i] - imagehash.phash(t)))
    neg = []
    for _ in range(n_negative):
        i, j = rng.sample(range(n_base), 2)
        neg.append(hashes[i] - hashes[j])
    roc = []
    for T in range(0, 33, 2):
        tpr = sum(1 for _, d in pos if d <= T) / len(pos)
        fpr = sum(1 for d in neg if d <= T) / len(neg)
        roc.append({"T": T, "recall": round(tpr, 4), "fpr": round(fpr, 4)})
    # chosen T: max recall with FPR <= 1%
    ok = [r for r in roc if r["fpr"] <= 0.01]
    chosen = max(ok, key=lambda r: (r["recall"], -r["T"])) if ok else roc[0]
    per_transform = {}
    for name in sorted({n for n, _ in pos}):
        ds = [d for n, d in pos if n == name]
        per_transform[name] = round(sum(1 for d in ds if d <= chosen["T"]) / len(ds), 4)
    at10 = next(r for r in roc if r["T"] == 10)
    out = {"n_base_images": n_base, "n_positive_pairs": len(pos), "n_negative_pairs": len(neg),
           "chosen_threshold": chosen["T"], "recall_at_chosen": chosen["recall"], "fpr_at_chosen": chosen["fpr"],
           "recall_at_10": at10["recall"], "fpr_at_10": at10["fpr"], "recall_by_transform": per_transform,
           "roc": roc}
    lines = [f"{n_base} generated base images x 6 transforms = {len(pos)} positive pairs; "
             f"{len(neg)} unrelated pairs. Threshold chosen = highest recall with FPR <= 1%.", "",
             *md_table(roc, ["T", "recall", "fpr"]), "",
             f"Chosen T = {chosen['T']}: recall {chosen['recall']}, FPR {chosen['fpr']}.", "",
             *md_table([{"transform": k, "recall": v} for k, v in per_transform.items()], ["transform", "recall"])]
    write_report("phash", "Perceptual-hash lineage: transformation suite", lines)
    return out
