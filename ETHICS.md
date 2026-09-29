# Ethics and responsible use

SATYA-NET is a prototype built for SIH 2026 PS 26152 (NTRO). These commitments
are enforced in code where possible, and the tests named below check them.

## What the system does not do
- **No individual demographic profiling.** Demographics are cohort counts only.
  Buckets under K_ANON (default 10) are withheld, and released counts carry
  Laplace noise (DP_EPSILON). No endpoint returns an account's inferred age,
  location or interests. Tests: `test_demographics.py`, `test_api.py`.
- **No "bot" labels.** Coordination scores describe *behaviour consistent with
  scripted amplification* and are presented as a statistical signal for analyst
  review, not an accusation. The experimental behaviour-likelihood score uses
  timing and content-reuse features only. It never uses demographics and is
  never labelled "bot".
- **No legal claims.** The Section 63 (BSA 2023) certificate is a DRAFT for review and
  signature. It is not a legal opinion, and no claim of admissibility is made.
- **No interaction with platforms.** Collectors only read public content. The
  system never posts, likes, follows or messages, and never touches private
  accounts or DMs.

## Data
- The demo runs on a **fully synthetic** scenario (fictional places, accounts
  and events; `synthetic=true` on every object; SIMULATED banner in the UI).
- Live collection uses research-grade tools (twscrape, Telethon, PRAW, YouTube
  Data API). twscrape uses X's internal API, which violates X's Terms of
  Service, so it is used with burner accounts only for the prototype. A
  production deployment must use licensed or official data access.
- Instagram and Facebook data enter only through analyst-supplied exports.
- Account ids used in demographic computation are pseudonymised with HMAC.

## Limitations (shown in the UI)
- Earliest *observed* origin is not necessarily the true origin.
- Sarcasm detection is English-biased, and the Hinglish results are weaker.
- Age inference covers few accounts and is coarse (bio cues only).
- Emotion metrics come from synthetic template labels. Gold-set evaluation is
  pending (human annotation task).
- Coordination weights were tuned on one synthetic seed. Real campaigns vary
  more, so expect lower recall on real data.

## Human in the loop
Alerts are ranked suggestions. Creating a case, exporting and generating a
certificate are analyst actions, and each is written to the tamper-evident audit
trail.
