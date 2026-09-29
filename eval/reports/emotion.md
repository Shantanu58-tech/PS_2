# Emotion inference evaluation

**Label source:** synthetic scenario template labels, not a human-audited gold set. Gold-set macro-F1 (PRD 11.1): not yet measured.

Evaluated on seed 11 (held-out); per-label thresholds tuned on the validation seed: {'anxiety': 0.42, 'sarcasm': 0.86, 'excitement': 0.5}. Models: zeroshot-mdeberta-xnli+xlmr-sentiment-v2. Baselines use threshold 0.5.

| label | model | precision | recall | f1 | tp | fp | fn |
|---|---|---|---|---|---|---|---|
| anxiety | pre-trained pipeline (ours) | 0.8604 | 0.7461 | 0.7992 | 191 | 31 | 65 |
| anxiety | zero-shot mDeBERTa NLI (baseline c) | 0.8315 | 0.5977 | 0.6955 | 153 | 31 | 103 |
| anxiety | lexicon (LEAKY: written with the templates) | 0.8604 | 0.7461 | 0.7992 | 191 | 31 | 65 |
| sarcasm | pre-trained pipeline (ours) | 0.1842 | 0.1591 | 0.1707 | 7 | 31 | 37 |
| sarcasm | zero-shot mDeBERTa NLI (baseline c) | 0.0516 | 1.0 | 0.0981 | 44 | 809 | 0 |
| sarcasm | lexicon (LEAKY: written with the templates) | 1.0 | 0.5455 | 0.7059 | 24 | 0 | 20 |
| excitement | pre-trained pipeline (ours) | 0.8563 | 1.0 | 0.9226 | 900 | 151 | 0 |
| excitement | zero-shot mDeBERTa NLI (baseline c) | 0.8563 | 1.0 | 0.9226 | 900 | 151 | 0 |
| excitement | lexicon (LEAKY: written with the templates) | 1.0 | 0.62 | 0.7654 | 558 | 0 | 342 |

Macro-F1: pre-trained pipeline 0.6308; zero-shot NLI baseline 0.5721; lexicon 0.7568. Hinglish subset macro-F1 (pipeline) 0.6229 (n=160).

**Caveat:** the lexicon was written by the same team that wrote the scenario templates, so it leaks the labels and is an upper bound, not a fair baseline. The fair comparison is the pipeline vs the zero-shot NLI baseline. English pre-trained models under-read anxious replies phrased as questions ("Is this real? Someone verify please") and the sarcasm model (news-headline trained) misses sarcastic debunks; this motivates the PRD 11 MuRIL fine-tune.

## Raw vs organic-only distortion (rumour window)

| raw_anxiety_share | organic_anxiety_share | distortion_ratio | raw_posts | organic_posts |
|---|---|---|---|---|
| 0.4196 | 0.6078 | 0.69 | 367 | 51 |

## Analysis: why the distortion ratio is below 1 (validation seed 7)
Mean anxiety per template shows the zero-shot model reacting to *words* like
"panic", "fear" or "dar" rather than to panic-spreading content:
"BREAKING: Varunapur Dam has cracked! Evacuate immediately!" scores 0.13 and the
Devanagari rumour 0.02, while the debunk "Stop spreading panic" scores 0.94.
Coordinated accounts post the rumour templates, so removing them *raises* the
organic anxiety share. The "bots made it look more panicked" claim is therefore
**not supported** by the current pre-trained models. It needs a fine-tuned
model (PRD 11, MuRIL) trained on panic-inducing rumours.
