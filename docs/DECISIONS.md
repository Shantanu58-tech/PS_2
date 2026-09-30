# Decisions log

Required by CLAUDE.md rule 10: every place where the implementation adapts to a
library, deviates from the PRD, or fixes a defect found in audit is recorded
here with the reason. Newest first within each section.

---

## 1. Analytics algorithms

### D-01 Coordination unit of analysis = narrative clusters, not topics
*PRD 8.V2.* The first implementation scored coordination per **topic**. When
topic clustering split the rumour into per-template topics (it does under the
hashing fallback, and partly with sentence embeddings for EN vs Hinglish
templates) most clusters fell below the size gate and recall collapsed
(11/60 on the mini scenario). Candidate clusters are now connected components
of posts linked by any of: near-identical text (cosine >= 0.90) **within the
same hour**, a shared hashtag **within the same 30-min window**, or an explicit
repost/forward chain (`origin_post_id`). The time bounds stop organic reuse of
common phrases from chaining the whole timeline together. Result on the mini
scenario with the hashing fallback: 60/60, 0 false positives.

### D-02 Per-account attribution inside a flagged cluster
Scoring every account in a flagged cluster with the cluster score would label
organic users who merely reply to a campaign. Each account gets its own score
from `co_sync` (near-duplicate post by a *different* account within 60 s),
`regularity` (max(0, -B) of its own gaps, needs >= 3 posts), `repetition`
and the cluster duplicate ratio. Flag threshold 0.7 (PRD).

### D-03 Cluster score: cross-account duplicate ratio + regular-share term
PRD formula `dup = share of posts with cosine >= 0.95 to the medoid` is ~0 for
paraphrased templates under semantic embeddings (similarities 0.84-0.94).
Replaced by the share of posts that have a near-duplicate (>= 0.90) from a
different account. The merged stream of many scripted accounts is *bursty*
(B > 0), so `max(0, -B)` of the merged stream carries no signal; added
`regular_share` = share of posts from accounts whose own cadence is regular
(B <= -0.5), weight 3.0. Weights were set on **seed 7** and are evaluated on
held-out **seed 11** (eval/reports/coordination.md), per PRD 8.V2.

### D-04 Goh-Barabasi burstiness returns -1 for perfectly periodic gaps
`burstiness()` special-cased sigma = 0 to return 0; the formula gives
B = (0 - mu)/(0 + mu) = -1, and PRD section 2 states "scripted bots are regular
(B -> -1)". The locked test `test_burstiness_regular` asserted the wrong value;
it now asserts -1 and a Poisson test (B ~ 0) was added. Scenario results are
unaffected (jittered cadences never have sigma exactly 0).

### D-05 Topic engine: windowed agglomerative clustering (BERTopic optional)
*PRD 8.D* asks for BERTopic per sliding window + centroid matching. Default is
average-linkage agglomerative clustering on the same multilingual embeddings
with c-TF-IDF labels, windowed (24 h, by post time) with centroid matching
(tau_match 0.80) and nearest-centroid assignment (tau_assign 0.55). Reasons:
deterministic (UMAP in BERTopic is stochastic, bad for reproducible evals),
~10x faster, and no Smart App Control issues. `TOPIC_ENGINE=bertopic` selects
BERTopic. The old code clustered only posts newer than "today 00:00 UTC", so
replayed history was never clustered; windows are now anchored on data time.

### D-06 Forecasting: gradient boosting + Hawkes instead of Holt's damped trend
PRD 8.D suggests Holt's damped trend (60-min horizon); Backlog B1 asks for a
Hawkes intensity forecast after a gradient-boosting baseline. Implemented B1:
GBR on lagged hourly counts (80% band from residual quantiles) and an
exponential-kernel Hawkes process fitted by MLE, horizon 6 h (hourly series).
Backtest MAE vs a naive last-value baseline is in the eval report. Holt is not
implemented.

### D-07 Signal priority components
P = 100 (0.35 B + 0.30 C + 0.20 S + 0.15 R) with B = min(1, level/5),
C = share of the burst's posts from coordinated accounts, S = min(1, |anxiety
shift| / 0.5) (burst window vs rest of topic; a simple proxy for PRD's CUSUM),
R = reach percentile among bursts. One alert per topic (strongest burst).
"High priority" = P >= 70. The previous coordinated-share SQL cross-joined
every post of the platform, so the "% coordinated" shown was meaningless.

### D-08 KOL ranking: cascade influence first; cascade = ancestors
Edges run interactor -> original author, so the accounts an author set off are
its **ancestors** (the old code used descendants and always reported 0).
Influence = 0.5 cascade + 0.3 PageRank + 0.2 betweenness, each normalised.
Betweenness sampling is seeded (seed 7) for stable rankings.

### D-09 Demographics: withheld buckets + Laplace noise
Buckets with a true count < K_ANON are withheld (only their number is
released; previously stored with a fabricated count = K). Released counts get
Laplace(1/DP_EPSILON) noise (sensitivity 1), rounded and floored at K so noise
never reveals a sub-K cohort. Results are recomputed (old code appended
duplicate rows on each run). Location matching is whole-word so short aliases
("up", "mp") no longer match "startup". Gazetteer: data/gazetteer/india.json
(36 states/UTs). Added a language dimension. Professional interests remain
keyword rules (PRD suggests embedding zero-shot; not done).

### D-10 Emotion model mapping and Hinglish blend
Pre-trained models (no fine-tune; MuRIL fine-tuning in PRD 11 needs a GPU and
a 400-item human-audited gold set - human task). Label mapping from
j-hartmann/emotion: fear, sadness -> anxiety; anger, disgust -> against;
joy, surprise -> excitement. For Hinglish text the lexicon scores
(data/lexicons/emotion_lexicon.json) are blended with max(). Model inputs are
de-duplicated after stripping @mentions/URLs, and scores are cached in
data/cache/emotion_cache.sqlite keyed by (text, model paths). The eval
measures agreement with the scenario's **synthetic template labels**, clearly
labelled; gold-set macro-F1 is "not yet measured".

## 2. Data pipeline and ledger

### D-11 Replay records bypassed the canonical normaliser (critical bug)
Scenario records use canonical field names (`post_id`, `author_id`) but were
routed to the platform-native normalisers (which read `id`, `author`), so
almost every post became `post_id="unknown"` and was deduplicated away.
Replay / canonical payloads now go through `normalize_synthetic`.

### D-12 Ingestion writes the ledger (previously it never did)
`ingest_record` only wrote posts/accounts/edges; nothing in the running app
appended to `raw_records`. Every record is now appended (hash-chained, signed
Merkle checkpoint per 100) **before** normalisation and posts carry
`ledger_seq`. Commits are per batch (`LedgerWriter.append(commit=False)`).

### D-13 verify_chain now recomputes checkpoint Merkle roots
It collected entry hashes but only checked checkpoint *signatures*; a
re-signed forged root passed. It now recomputes each root from the covered
entries. Regression test: `test_checkpoint_root_must_match_entries`.

### D-14 Tamper simulation on a temp-dir backup
The old endpoint copied the DB and ran UPDATE with the append-only trigger
still present (it would have raised) and left the scratch file beside the real
DB. Now: SQLite backup API into a temp dir, trigger dropped on the copy only,
copy deleted afterwards.

### D-15 Audit trail is part of the hash chain
Analyst actions write `audit_log` and a ledger entry (collector_id "audit")
through the **same** LedgerWriter as ingestion; a second writer would cache
its own prev_hash and fork the chain.

### D-16 OpenTimestamps: stamp the newest checkpoint per run
Because entry hashes chain every earlier entry, anchoring the newest
checkpoint root transitively timestamps the ledger up to its last_seq. One
stamp per analytics run (ENABLE_OTS=true). `upgrade()` pulls Bitcoin
attestations from the calendars; `verify_bitcoin()` checks the attested
merkle root against the block header from blockstream.info (no local node).
Tests and evals force ENABLE_OTS off.

### D-17 Replay is not paced by simulated time; double replay refused
Records are ingested in created_at order in batches of 250 (the demo needs
the full 7 days in minutes). `/api/replay/start` refuses a second run because
the append-only ledger would record every item twice (`force=true` to append
a second collection run deliberately).

### D-18 Paths resolve against the repo root
Docker mounted repo-root `data/ models/ replay/` while local runs resolved
them under `backend/`. All relative path settings now resolve against the repo
root (which is "/" in the container; compose mounts at /data, /models,
/replay). Ledger keys live in data/keys (private key gitignored).

### D-19 Interaction edges are account -> account
Reply/repost edges pointed at the parent *post id*; they now resolve to the
parent's author (late parents resolved after ingest). @mentions resolve
handle -> account id.

## 3. Library adaptations (collectors)

### D-20 twscrape 0.20
`AccountsPool.add_account_cookies` no longer exists; cookie login is
`add_account(username, password="", email="", email_password="", cookies=...)`.
Tweet JSON fields used: `id, rawContent, date, user{id, username, displayname,
rawDescription, created, followersCount, friendsCount, location, verified},
inReplyToTweetId, retweetedTweet, quotedTweet, conversationId`. The X
normaliser now maps `location`, `created`, `verified` (demographics needs them).

### D-21 Telethon forward headers kept structured
`fwd_from` was stored as `str(object)`. Now `{from_id, channel_post, date}`;
the normaliser builds `origin_post_id = "<from_id>_<channel_post>"`.
Replies map to `<channel>_<reply_to_msg_id>`.

### D-22 YouTube: replies included, authors keyed by channel id
`commentThreads.list(part="snippet,replies")` replies were dropped and authors
keyed by display name. Replies are emitted with `parent_id`; author =
`authorChannelId.value`. PRAW and the YouTube client are synchronous and now
run in worker threads (they blocked the event loop).

### D-23 Reddit comment kind rule kept
A comment whose parent is a submission (`t3_`) is labelled `kind="post"`, as
the locked normaliser test expects; only replies to comments (`t1_`) are
`comment`. `parent_post_id` now strips the `t1_/t3_` prefix.

### D-24 Instagram / Facebook via export import
No free live API for public posts; `app/collectors/import_csv.py` ingests
Meta Content Library / CrowdTangle-style CSV through the same ledger path
(`POST /api/import/{instagram|facebook}`). Stated as import-only in the UI.

## 4. Environment and tooling

### D-25 Windows Smart App Control pins (supersedes ADR 0004's uv cutoff)
ADR 0004 describes a `[tool.uv] exclude-newer` cutoff, but it was not present
and uv is not installed. Observed blocks and the pins that load:
ruff 0.16.9 -> **ruff 0.12.0**; pandas 3.0.6 (tzconversion DLL) -> **pandas
2.2.3** (<3); scikit-learn 1.9.1 (_gradient_boosting DLL) -> **1.6.1** (<1.7).
torch 2.14 CPU, transformers 5.17, sentence-transformers 6.1, hdbscan, faiss,
opencv load fine. Linux (Docker/CI) is unaffected.

### D-26 pyproject build backend
`setuptools.backends.legacy:build` does not exist, so `pip install -e .`
(`make setup`) failed. Now `setuptools.build_meta`.

### D-27 Model locations
`scripts/fetch_models.py` downloads the CLAUDE.md models into `models/`
(safetensors/PyTorch weights only; ONNX/OpenVINO copies skipped).
`app.nlp.models.resolve()` prefers `models/<org>--<name>` over the hub id.
`EMBED_BACKEND=hashing` / `EMOTION_BACKEND=lexicon` select deterministic
fallbacks for CI; outputs are labelled (`model_version="lexicon-v1"`).

### D-28 Next.js scaffold leftovers
`frontend/src/app/*`, `Sidebar.tsx`, `EngineStatus.tsx`,
`SectionPlaceholder.tsx`, `ProvenanceBadge.tsx`, `lib/api.ts`, `lib/nav.ts`
belong to an abandoned Next.js scaffold; the app is Vite + react-router
(`src/App.tsx`). They broke `npm run build` (tsc). They are excluded in
tsconfig pending the team's approval to delete them.

### D-29 LLM summaries use Gemini
Team decision: Backlog B4 uses Google Gemini (`google-genai`,
`GEMINI_API_KEY`). Prompt-injection defences and break tests:
app/analytics/summarize.py, tests/test_summarize.py.

### D-30 Dead `app/api/health.py`
Imported a non-existent `get_settings`; nothing used it (`main.py` wires
`routers/health.py`). Reduced to an alias of the live router.

### D-31 transformers "incorrect regex pattern" warning on the XLM-R tokenizer
transformers 5.x warns that the cardiffnlp XLM-R tokenizer has an incorrect
pre-tokenizer regex (a Mistral-specific check). Verified as a false positive:
the fast tokenizer's output is identical to the reference SentencePiece model
on English, Hinglish, Devanagari and all-caps samples. `sentencepiece` is a
declared dependency so the slow path is also available.

### D-32 Emotion engine: zero-shot NLI + XLM-R polarity; "anxiety" = panic in the conversation
The eval showed the classifier pipeline (XLM-R sentiment + English emotion +
sarcasm models) scoring macro-F1 0.28 on synthetic labels, while PRD baseline
(c), zero-shot multilingual NLI (mDeBERTa-v3 XNLI), scored 0.64. The engine
is now NLI for anxiety / excitement / sarcasm plus the XLM-R sentiment model
for supportive / against (generic "supports/opposes" hypotheses entail almost
every post). `EMOTION_ENGINE=classifier` keeps the old pipeline.
Per-label thresholds are tuned on validation seed 7 only
(`eval/calibrate_emotion.py` -> `app/nlp/emotion_thresholds.json`); headline
metrics are reported on held-out seed 11.
The first NLI hypothesis for anxiety ("The author is anxious, afraid or
worried") only fired on first-person worry, so panic-spreading broadcasts
("Evacuate NOW!") scored low and the raw-vs-organic distortion inverted. PS
26152 / PRD use anxiety in the sense of *panic in the conversation*, so the
hypothesis was changed to "This message expresses or spreads fear, panic or
alarm." This definition change was made after seeing seed-7 descriptive
results; thresholds were re-tuned on seed 7 and held-out numbers recomputed.
Sarcasm remains weak for every pre-trained option (see eval/reports/emotion.md).

## 5. Hosting

### D-33 Public demo on Render (free), kept awake by a Cloudflare cron Worker
Live: https://deepastambha.onrender.com. Same pattern as the team's TRIVENI deployment, replicated
without touching it: a Docker web service whose image carries no private
data; a private Hugging Face dataset repo (`ZOROxJODD/deepastambha-bundle`) supplies
the analysed demo database and ledger signing key at start-up (`HF_TOKEN`
secret); the Cloudflare Worker `deepastambha-keepalive` pings `/healthz` every 10
minutes.
- Hugging Face Docker Spaces now need PRO on free CPU (HTTP 402), so Render is used.
- The service runs in a **separate Render account/workspace**: free web services
  share 750 instance-hours per workspace, and TRIVENI (kept awake 24/7) already
  uses ~744 h in its workspace, so a second always-on service there would get
  every free service in it (including TRIVENI) suspended.
- The hosted demo needs no ML models (analytics precomputed in the bundled DB):
  runtime requirements only, peak memory 251 MB (512 MB limit). KOL/bridge
  rankings are precomputed (`influence_cache`) because centrality took ~30 s per
  request locally and timed out on 0.1 CPU. Bundles are packed from a
  WAL-checkpointed, DELETE-journal copy (a WAL database loses uncheckpointed rows).
- `DEMO_READONLY=true` blocks every write except verify, the tamper simulation,
  case/brief generation and LLM summaries (PRD 12). Container storage is
  ephemeral: visitor-created cases vanish on restart.
- Render builds from a private deployment mirror that the local repo updates in
  the same push as the canonical repository (see deploy/render/README.md).

### D-34 Gemini model alias with fallback
`gemini-2.5-flash` is retired for new keys. The default is the
`gemini-flash-latest` alias, with fallback to `gemini-3.8-flash` and
`gemini-flash-lite-latest` on 404 (retired) and retry on 429/503 (overload).
The model that answered is stored with each summary. Tests blank every
credential through environment variables so they can never call real services,
even when backend/.env holds real keys.

### D-35 Clean product UI (overrides the on-screen SIMULATED banner)
The team asked for a clean, uncluttered hackathon product site rather than a
compliance console. The UI now follows the look of the team's Deepentra project:
light theme by default, white rounded cards, pill controls and a flat sidebar
with a new DEEPASTAMBHA logo (shield + watchful eye with a network pupil). Removed
from the UI: the SIMULATED/SIH/team banner, requirement codes in the nav, the
Sources and PS 26152 & Eval pages, and long methodology notes (short popovers
remain). The problem-statement mapping and evaluation numbers live in the PPT and
in `eval/reports/`. Records still carry `synthetic=true` in the data layer, and
the backend endpoints for collectors, evaluation and traceability are unchanged.
This deliberately departs from CLAUDE.md rule 7 (SIMULATED banner) at the
team's request.

### D-36 Platform views, viral hashtags, segment spread, IG/FB demo sample
- **Platforms page** (`/api/platforms`, `/api/platforms/{p}`): one view per source with its connection
  state (connected / API ready / official export / sample data), activity, mood, top topics, most active
  accounts and latest posts. The Emotions page filters by platform and by posts vs comment threads
  (`kind=posts|comments` on `/api/timeline/emotions` and `/api/timeline/compare`).
- **Viral hashtags** (`/api/keywords/trending`): each hashtag's busiest hour divided by its usual hourly
  rate over the whole period (peak ≥ 10 posts), plus most-used. A trailing-window growth ranking was tried
  first but is uninformative when the data ends on a quiet day.
- **Segment spread** (`/api/graph/segment-spread`, analytics stage `segments`): segment 0 is the
  coordinated group; segments 1–4 are the largest greedy-modularity communities of the remaining
  interaction graph, named by their members' dominant platform. Short-lived narratives use 10-minute
  buckets. Precomputed like `influence_cache` because community detection is too slow per request on the
  free server.
- **Instagram/Facebook demo data**: `scenario/meta_export_sample.py` writes a fictional Meta-export-style CSV
  (about 1,000 rows each, every row `synthetic=true`), ingested through the real import path
  (`app/collectors/import_csv.py`, ledger → normaliser → analytics). The importer now honours a `synthetic`
  column so sample rows stay labelled; real exports default to `synthetic=false`.
- **UI**: hamburger (☰) toggle collapses the sidebar to icons on desktop and opens a drawer on mobile; the
  logo was simplified to a flat shield with a single eye.

### D-37 National Situation Room and one connected flow
The team asked for a first page that works as a national situation room and for a visible flow.
- **`/api/situation`** (`app/analytics/situation.py`) builds one cached aggregate: a plain-language
  situation report, KPIs, sectors, states, narratives being pushed, and hot topics.
  - **Sectors.** Each topic is assigned to one of nine sectors by transparent keyword evidence in its
    label, keywords and sample posts. Levels: critical = a manufactured topic with a high-priority
    signal; elevated = manufactured or ≥10% coordinated; watch = ≥2% coordinated or burst level ≥3;
    quiet = no posts.
  - **States.** A state is inferred only from the public profile location. A state is released only
    when ≥ K_ANON distinct accounts back it. Its impact counts posts in a manufactured narrative *or
    replies to one*: the coordinated accounts have no locations, and the real public reacts through
    replies.
  - **Hot topics.** Ranked by the busiest hour against the topic's usual hourly rate over the whole
    window.
  - **Caching.** The result is cached per data version and warmed at start-up; it takes about 0.3 s
    on 39k posts.
- **Analyst review** (`POST /api/alerts/{id}/review`): approve (opens a case), watchlist or dismiss.
  Every decision goes into the audit trail, and so into the hash chain. This makes the architecture
  diagram's Analyst Review, Watchlist and Case File branches real. It is allowed in the read-only
  demo, and is reset on restart.
- **Network nodes** now carry platform and followers. Edges carry their time. `/api/graph/node/{id}`
  returns public profile fields, activity per platform, topics, and connected accounts in both
  directions. It returns no inferred demographics.
- **UI.**
  - Uses the team's reference palette (sih30): espresso masthead with a tricolour strip, sand
    canvas, copper accent.
  - A numbered flow bar (1 Situation Room → 2 Detect → 3 Investigate → 4 Evidence) sits under the
    masthead. The same stages group the sidebar, head every page, and drive a "Next in the flow"
    card on each page.
  - Deep links (`?topic=`, `?sector=`, `?account=`, `?case=`) make every first-page element one
    click from its detail.
- **India map.** It is an equal-area tile grid, not a geographic outline. The `@svg-maps/india`
  outline that another tool added to the working tree predates the 2019 J&K/Ladakh reorganisation
  and may not follow the official boundary, which would be a problem on an NTRO demo. The tile grid
  sidesteps that and keeps small states clickable.

### D-38 Logo: the deepastambha
The shield-and-eye mark was too close to other teams' logos (the earlier working name was shared by several SIH 2026 teams, and security logos lean on shields, eyes, fingerprints and locks). The new mark is a deepastambha, the Indian temple lamp tower that keeps a light burning through the night, inside a round seal (echoing TRIVENI's seal). The six lamps on three tiers are the six platforms watched; the saffron flame is the sentinel, with listening arcs; a green base line completes the tricolour. A searched check (web, GitHub repositories of similarly named projects) found no product using this motif. Below 28px the dotted ring and outer arcs are dropped. Original emblem, not an official insignia.

### D-39 Renamed to DEEPASTAMBHA
The earlier working name is used by several government apps and other SIH 2026 teams. The product is now **DEEPASTAMBHA (दीपस्तम्भ, "pillar of light")**, matching its lamp-tower emblem (D-38). A GitHub search found no repository named "deepastambha"; "deepstambh" appears only as NGO websites. Every mention of the old name was then removed, including deployed identifiers: the Render service and URL (`deepastambha.onrender.com`), the `deepastambha-keepalive` Worker, the private bundle `ZOROxJODD/deepastambha-bundle` (a new repository; the old one is left for the owner to delete), the database file `data/deepastambha.db`, and browser-storage keys.

### D-40 Live Telegram feed on the public demo
The user connected their Telegram account (two-step login) and approved putting the session on the hosted demo, so the site can show real data next to the synthetic scenario. `GET /api/live/telegram` fetches the latest posts from a **fixed allowlist** of public news channels (`LIVE_TG_CHANNELS`: The Indian Express, Hindustan Times, Mint and Moneycontrol, all active on 2026-09-30). Visitors cannot choose channels. Results are cached (10 min on success, 2 min on failure) so any number of visitors causes at most one fetch per period. Posts are scored with the lexicon model (the free server has no GPU) and tagged with a sector only on strong keyword evidence. They are **shown, not stored**: putting 2026 posts into the Nov-2024 scenario would distort every timeline. `TG_API_ID`, `TG_API_HASH` and `TG_SESSION_STRING` are Render secrets. The session grants account access, so revoke it in Telegram (Settings > Devices) after the hackathon. Telethon was added to the runtime image.

### D-41 Review fixes: fresh dates, neutral data, faster pages, phone layout
A reviewer's walkthrough found the demo easy to see through and slow. What changed:
- **Dates.** `scripts/build_demo_bundle.py` regenerates the scenario anchored to the build time (`--anchor now`), so the incident sits in the last seven days. Every displayed date includes the year. Re-run it before a demo.
- **No give-aways.** Account and post IDs are random numbers (`acc_52747`), handles look like real people, and topic names come from the most central post rather than joined keywords.
- **Stance.** Each post is tagged spreading / questioning / debunking / reacting by rule (`analytics/stance.py`). Only spreading posts count towards spread; debunks no longer inflate the numbers. The AI summary lists claims and rebuttals separately.
- **Reach.** Influencer reach is two-hop, so it no longer saturates at one value.
- **Speed.** Heavy endpoints are cached per data version (`api/cache.py`) and warmed at start-up, and five read-path indexes were added. On the 0.1-CPU host, topics went from 6.5 s to milliseconds after the first call.
- **Audience.** It can be scoped to the people posting about one topic (`/api/demographics?scope=topic:<id>`), computed on request under the same k-anonymity and noise rules. It reports what it counted (accounts, how many, which dates). Unknowns are a note, not a bar.
- **Image copies** are grouped into one family per picture with thumbnails (`/api/media/{id}` serves only files inside `MEDIA_DIR`).
- **Phone layout.** The shell grid used `1fr`, which cannot shrink below its widest header, so every page was 738 px wide on a 390 px phone. It now uses `minmax(0, 1fr)`, and the smoke suite checks every route at phone width.
- **No data-source labels** in the UI (no "sample", "CSV" or "simulated" tags), except a genuine Live badge. The draft legal certificate still states when records are synthetic, because a certificate must be accurate.

### D-42 Live feeds on four platforms (X, Telegram, YouTube, Reddit)
The hosted demo had only Telegram live, although the X cookies (burner account) and the YouTube key had been verified locally. With the user's approval both went onto Render, and the live feed became one module (`collectors/live_feed.py`) with a fetcher per platform:
- **X:** twscrape user timelines of @PIB_India, @PIBFactCheck, @ndmaindia and @ANI (reposts skipped). twscrape is pinned to 0.20.1 because its cookie-login call changed in 0.20.
- **YouTube:** the channel's official RSS feed for new videos (free, no quota), plus Data API `commentThreads` on the two newest videos per channel (one quota unit per call; the 10-minute cache keeps a day far below the free 10,000).
- **Reddit:** the official subreddit RSS feed, one combined request for r/india+IndiaSpeaks+indianews (Reddit rate-limits rapid repeats). On Render it failed: Reddit refuses anonymous requests from cloud-server addresses. With `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` (a free "script" app) the feed uses Reddit's official API with an app-only token instead; until then the Reddit Live badge stays off and the page says why.
- **Telegram:** unchanged.
All sources are fixed in settings (`LIVE_X_ACCOUNTS`, `LIVE_YT_CHANNELS`, `LIVE_REDDIT_SUBS`, `LIVE_TG_CHANNELS`); visitors cannot choose them. Each platform is cached for 10 minutes (2 on failure), and posts are shown, not stored. **Instagram and Facebook have no live feed:** Meta offers no public feed or free API for other people's pages, third-party "RSS bridges" scrape against Meta's terms, and the team's own brief rules out unauthorised scraping. They stay on the official-export path; production would use Meta's Content Library. Parsers are tested offline with saved sample feeds.
