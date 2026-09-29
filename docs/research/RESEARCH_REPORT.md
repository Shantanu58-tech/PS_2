# SIH26152 "Social Media Analytics" (NTRO): Evidence Map, Gaps and a Differentiated Angle for Team MOGGERS

The five-component pipeline is already a crowded idea: at least nine public SIH26152 repos build the same FastAPI + React + NetworkX + "IndicBERT/XLM-R" dashboard. Your best chance to win is to be the team that is **measurably right on Indian code-mixed text, tracks narratives across Telegram and X, and is compliant by design**. Very few competitors, and no product we could verify, do all three.

## TL;DR
- **The idea is common; doing it rigorously is not.** Public SIH26152 repos converge on the same stack. They show seeded or "demo" data, lexicon or unevaluated transformer sentiment, per-user demographic guesses and D3 force graphs. Almost none publish accuracy on Hinglish, and almost none respect Telegram's API terms, which forbid using Telegram data for ML.
- **Evidence-backed gaps:** (1) Hinglish sarcasm and stance detection. The best SemEval-2020 SentiMix Hinglish score is 75.0% weighted F1 on only 3 classes, the top 15 teams all fall between 75% and 68.6% (Patwa et al.), and sarcasm datasets are tiny and imbalanced. (2) Indian demographic inference. M3's age F1 is 0.522\[1\] and it was validated on European languages. (3) Bot detection after the API shutdown. Botometer X is archival and blind to generative-AI bots. (4) Cross-platform (Telegram↔X) temporal spread. (5) Compliance-by-design under DPDP 2023/2025 and platform terms of service.
- **Recommended angle:** a compliance-first "narrative forensics" engine for India. It would offer calibrated Hinglish affect with abstention and a published evaluation card, and coordination detection on Telegram co-forward and X co-retweet (behaviour, not "bot scores"). It would add cross-platform cascade lineage and aggregate-only, k-suppressed demographics, with every alert tied to evidence posts.

## Key Findings

**1. What the problem statement really asks, and why NTRO**
- NTRO is India's specialised technical intelligence agency, formed in 2004. Its surveillance work reportedly includes internet monitoring.\[2\] The Wikipedia list of Indian intelligence agencies shows it under the Prime Minister's Office, covering SIGINT/TECHINT (secondary source; NTRO publishes little).\[3\]
- The operational need is concrete. Meta's Q3 2023 Adversarial Threat Report removed a China-origin network that "targeted primarily India and the Tibet region." The network ran two clusters of fictitious personas, one aimed at Tibet and one at India's Arunachal Pradesh region, posing as journalists, lawyers and human-rights activists on Facebook and X. It had 13 Facebook accounts and seven Groups, about 1,400 accounts joined one of the Groups, and content was mostly English with some Hindi. In the same report, a separate China network of 4,789 accounts had a portion switch "from posing as Americans to posing as being based in India." Meta's own Q1 2024 Adversarial Threat Report describes another China-origin network (37 Facebook accounts, 13 Pages, five Groups, nine Instagram accounts) that "targeted the global Sikh community, including in Australia, Canada, India, New Zealand, Pakistan, the UK, and Nigeria" through a fictitious "Operation K."
- **Read components A–E as an influence-operations workflow, not marketing analytics.** A = collection with provenance. B = affect and stance as a narrative signal. C = audience composition, strictly aggregate. D = emergence and early warning. E = who amplifies, and how narratives cross communities and platforms. That workflow is what "coordinated inauthentic behaviour" (CIB) analysis needs.\[4\]
- **The political risk is real and has precedent.** In 2018 the I&B Ministry's "Social Media Communication Hub" RFP sought a "360-degree view of the people who are creating buzz" across 716 districts. On 13 July 2018, in Mahua Moitra v. Union of India, a bench of CJI Dipak Misra and Justices A.M. Khanwilkar and D.Y. Chandrachud said it would be "like creating a surveillance state." On 3 August 2018 Attorney General K.K. Venugopal told the Court the proposal was withdrawn. A winning pitch must be visibly aggregate, auditable and minimisation-first, or judges will see an SMCH clone.
- **The adjacent state tooling is takedown, not analytics.** The MHA/I4C Sahyog portal (launched October 2024) automates Section 79(3)(b) takedown notices.\[5\] More than 2,300 blocking orders went to 19 platforms between October 2024 and October 2025; per Indian Express RTI data, WhatsApp got 1,392, YouTube 176 and Instagram 169. By July 2025, 16,484 links had been taken down. X called it a "censorship portal," but the Karnataka High Court dismissed X's petition on 24 September 2025, calling Sahyog "an instrument of public good." X appealed in November 2025, and the Supreme Court has since stayed High Court challenges (per The Wire and NorthEast Now). Takedown workflows exist; the analytic layer that justifies action with evidence is the gap.

**2. The five components against the state of the art (one-line verdicts)**
- A (ingestion): legally and financially the hardest part in 2026 (see Practical Reality).
- B (nuanced affect): the weakest part scientifically for Hinglish.
- C (demographics): the weakest part ethically and scientifically.
- D (trends): mature (BERTopic-style clustering plus burst detection). It is easy to match, hard to stand out on.
- E (network/KOL): PageRank and betweenness are commodities. Temporal, cross-platform coordination is where the frontier lies.\[6\]

## Details

### "This is what I found" — structured inventory

**A. Research papers, models and datasets**

| # | Name | Type | Open? | What it does | Covers | Limitations (stated or obvious) |
|---|---|---|---|---|---|---|
| 1 | SemEval-2020 Task 9 SentiMix (Patwa et al.) | Paper + dataset | Open | Hinglish/Spanglish code-mixed tweet sentiment, 20K Hinglish examples with word-level language IDs | B | Only 3 classes (pos/neg/neutral). Best Hinglish score was 75.0% weighted F1 across 61 teams, with the top 15 between 75% and 68.6%. Authors: "Properly annotated code-mixed data is still scarce" |
| 2 | Swami et al. 2018 Hinglish sarcasm corpus | Dataset + paper | Open | About 5,000 Hinglish tweets labelled for sarcasm; random forest/SVM, F1 78.4% | B | Highly imbalanced, "just 10% of sarcastic tweets," so results are "quite skewed" (per the arXiv 2202.02702 review) |\[7\]
| 3 | Aggarwal et al. 2020, "Did you really mean what you said?" | Paper | Open | Deep learning with bilingual FastText/Word2Vec on 427k Hinglish + 300k English tweets for sarcasm | B | Pre-transformer; Hinglish+English F1 79.4% |\[7\]\[8\]
| 4 | "How Effective is Incongruity?" (arXiv 2202.02702) | Paper | Open | Incongruity-based code-mixed sarcasm | B | Notes prior work does not handle incongruity |\[7\]
| 5 | MaSaC / MSH-COMICS | Dataset + model | Open | First Hindi-English multimodal sarcasm/humour dataset for conversational dialogue | B | TV-dialogue domain, not social posts |\[9\]
| 6 | Explainable sarcasm in imbalanced code-mixed text (Arabian J. Sci. Eng., 2026) | Paper | Closed (Springer) | mBERT-GRU with contextual augmentation and focal loss | B, explainability | Authors: augmentation "frequently adds noise to code-mixed texts" |\[10\]
| 7 | Sarcasm in Hindi-Hinglish: A Systematic Survey (Springer, 2025) | Survey | Closed | Maps the field | B | Detection "doubled" in difficulty for code-mixed text |\[11\]
| 8 | Elevating code-mixed text via auditory information (arXiv 2310.18155) | Paper | Open | Uses Hinglish sentiment (Joshi 2016, 3,879 FB posts) and HOT offensive (3,189 tweets) benchmarks | B | Small benchmarks |\[12\]
| 9 | M3 Inference (Wang et al., WWW 2019) | Model + repo | Open | Age, gender and organisation status from profile image, name and bio in 32 languages | C | Macro-F1: gender 0.918, **age 0.522**, org 0.898. Age F1 varies by language from 0.28 to 0.73. Multilingual evaluation was European. Uses profile images\[13\] |\[1\]\[14\]
| 10 | twitter-poststratification (euagendas) | Repo | Open | Reweights inferred demographics toward census-representative estimates | C | EU census regions only |\[15\]\[16\]
| 11 | DADIT (arXiv 2403.05700) | Dataset + comparison | Open | Italian demographic classification; compares M3, computer vision and XLM-R | C | Italian; shows fine-tuned XLM-R alternatives |\[17\]
| 12 | TwiBot-22 (NeurIPS 2022 D&B) | Benchmark | Open | Largest graph-based Twitter bot benchmark; 35 baselines re-implemented across 9 datasets | CIB/bot, E | Top-5 models are graph-based. Performance drops about 2.7% on average versus TwiBot-20 as bots evolve. Scalability issues |\[18\]\[19\]
| 13 | BotMoE (arXiv 2304.06280) | Model | Open | Community-aware mixture of experts for bot detection | CIB/bot | Twitter-only; relies on pre-2023 data |\[20\]
| 14 | Social Media Bot Detection review (arXiv 2503.22838) | Survey | Open | Literature review | CIB/bot | Confirms graph methods lead |\[21\]
| 15 | Coordination Network Toolkit (J. Comput. Soc. Sci., 2024) | Tool + paper | Open | Multi-behaviour coordination: co-retweet within 60 s, co-tweet, co-link, co-mention, co-reply, as weighted multigraphs\[22\] | E, CIB | Detects coordination, not intent |
| 16 | Influence of coordinated behaviour in cascades (arXiv 2609.24398) | Paper | Open | Post-hoc evaluation of coordinated accounts' impact on diffusion | E, temporal spread | Labels mean "coordinated behavior rather than verified inauthentic behavior"\[4\] |
| 17 | CIB on TikTok (arXiv 2505.10867) | Paper | Open | Co-duet, co-stitch and co-reply signals | CIB | Reports negative results: many signals found organic partisanship, not CIB\[23\] |
| 18 | CIB on alternative platforms (ICWSM 2025 workshop) | Paper | Open | URL and text similarity networks via the Open Measures API across Gab, VK and others | CIB, cross-platform | Alternative ecosystems "remain understudied"\[24\] |
| 19 | vera.ai Coordinated Sharing Behaviour conference report (2024) | Report | Open | Summarises the state of the field | CIB | Cites unclear CIB definitions, restricted data access and generative AI as open problems; points to cross-platform detection as a frontier\[6\]\[25\] |
| 20 | Pushshift Telegram Dataset (ICWSM 2020) | Dataset | Open | 27,801 channels, 317,224,715 messages, 2.2M users | A, D, E | Data ends November 2019. Seeded from right-wing and crypto channels (per the TGDataset critique) |\[26\]\[27\]
| 21 | TGDataset (arXiv 2303.05345) | Dataset | Open | About 4× Pushshift's channel count, heterogeneous seeds | A, D, E | Channels only; no groups |\[27\]

**B. Commercial and institutional tools**

| # | Name | Type | Open? | What it does | Covers | Limitations |
|---|---|---|---|---|---|---|
| 22 | Cyabra | Product | Closed | Authenticity scores for accounts and narratives; monitors X, Telegram, TikTok and Reddit; new "Coordinated Activity Detection" AI agent; named a Market Shaper in Gartner's June 2026 Emerging Market Quadrant for Narrative Intelligence\[28\]\[29\]\[30\]\[31\] | A, B, D, E, CIB, real-time | Opaque scoring; custom pricing; no public Hinglish evaluation. Founded by Israeli intelligence veterans, a sovereignty concern for Indian agencies\[28\]\[32\] |
| 23 | Logically Intelligence | Product | Closed | "Situation Rooms," narrative detection, any-language Boolean queries with translation\[33\] | A, D, E | Translate-then-analyse loses code-mixed nuance |
| 24 | Graphika | Product/services | Closed | AI-generated maps of social media landscapes; network investigations\[33\] | E, CIB | Analyst-led services; not self-serve |
| 25 | Blackbird AI, Alethea | Products | Closed | Narrative and threat intelligence, listed as Cyabra competitors\[28\] | D, E, CIB | Not evaluated in detail here |
| 26 | OSINT Monitor (osintmon) | Product | Closed | Government-oriented multilingual sentiment and trends, including code-mixed "Arabizi" | A, B, D | Arabic-focused. Shows that commercial code-mixed support exists, but not for Hinglish |\[34\]
| 27 | Social Links | Product | Closed | OSINT across 500+ sources, including messengers and the dark web\[35\] | A, E | Investigation of individuals, the opposite of aggregate |
| 28 | Meta Content Library | Research tool | Closed (vetted) | Public Facebook/Instagram archive with comments; CrowdTangle's successor | A (FB/IG) | Academic and non-profit only; slow access (11 applied, 4 granted in one survey); SOMAR free compute ended 31 December 2025 |\[36\]\[37\]
| 29 | Botometer X / Botometer Pro API (OSoMe) | Tool | Free, closed model | Bot scores | CIB/bot | Archival scores from data collected before June 2023. BotometerLite "does not have the ability to detect bots supercharged by AI." v4 and Lite endpoints shut down on 2 November 2026\[38\]\[39\] |
| 30 | Hoaxy2, Coordiscope (OSoMe) | Tools | Free | Diffusion visualisation (Bluesky, or X with your own keys); BLOC-based behaviour comparison | D, E | Hoaxy "no longer provides bot scores"\[40\] |
| 31 | Mainstream social listening (Brandwatch, Talkwalker, Meltwater, Sprinklr, Pulsar) | Products | Closed | Brand listening | A, B, D | **Not verified in this research pass.** Treat any matrix cells for them as unverified |
| 32 | Sahyog portal (MHA/I4C) | Government system | Closed | Takedown-notice workflow\[5\] | None of A–E (enforcement only) | Karnataka HC dismissed X's challenge on 24 Sep 2025; X's appeal followed, and the Supreme Court has stayed HC challenges (The Wire) |
| 33 | SVPNPA NDCRTC "OSINT & Social Media Analysis" course | Training | n/a | Trains police in sentiment, trend and profiling analysis\[41\] | Training only | Shows demand inside Indian law enforcement |
| 34 | Social Media Communication Hub (I&B RFP, 2018) | Withdrawn procurement | n/a | Proposed 360° monitoring | A–E | Withdrawn after Supreme Court scrutiny |\[42\]

**C. GitHub / SIH26152 competitor repos**

| # | Repo | Approach | A–E claimed | Platforms actually wired | Stack | Weakest point |
|---|---|---|---|---|---|---|
| 35 | RudraSuthar-web/SIH26152-Social-Media-Analysis | "Sovereign" threat-intelligence framing: botnet clusters, panic/hostility, centralities, cascade propagation | A–E + CIB | X, Telegram (Telethon user session), web | FastAPI, SQLAlchemy/Alembic, WebSockets, RSA-JWT | README shows what appear to be real Telegram API_ID/API_HASH values (a security failure); Telethon use conflicts with Telegram ToS 1.5 if data feeds ML |\[43\]
| 36 | omghotekar01-dotcom/SOCIAL-MEDIA---PS152 (NEXUS) | "Track ideas, not hashtags"; labels every event LIVE/REPLAY/IMPORT; "origin" means earliest observed | A–E + explainable alerts | Official X API, Telegram **Bot API**, YouTube, Meta, CSV replay | FastAPI + Spring Boot gateway + React/TS | The Bot API only receives messages from chats the bot belongs to, so it cannot monitor arbitrary public channels |\[44\]\[45\]
| 37 | Shubham2025-ai/NEXUS_SIH26152_FULL_PROJECT | Same NEXUS concept; "free-first"; requirement→code→UI traceability doc; free-source matrix; 5-minute jury script | A–E | Meta ig_hashtag_search, public-profile fallback, replay | Similar | **Strongest honesty/traceability competitor.** "Public bridge" fallbacks may breach terms of service |\[46\]
| 38 | MrManasss/net-sentinel-social (+ tanishkafanse clone) | Four parallel engines; SHA-256 tamper-evident audit chain; 6-class taxonomy (Supportive/Against/Anxious/Excited/Sarcastic/Neutral) via IndicBERT/XLM-R; Hindi-English sarcasm | A–E + CIB | Telegram, Reddit, YouTube, X | Not fully visible | No published metrics; the hash chain is the only "blockchain" nod, and it is easy to copy |\[47\]
| 39 | Krishna-Das20/SIH-26152 = Rishiraj-De/SIH-26152 (identical READMEs) | "Serverless"; 7-vector emotion; sarcasm index; timeline scrubber | A–E | Telegram, Reddit JSON, YouTube v3, X (+ IG/FB claimed) | D3 force graph | Infers **per-user age brackets including "<18"**, a DPDP s.9 children's-data red flag; duplicated repos |\[48\]\[49\]
| 40 | singharyan-912/Traject | Engineering-first: canonical Pydantic v2 schema with UTC enforcement, immutable raw JSONL, Parquet, deterministic Telegram IDs, replay engine; RoBERTa and XLM-R **evaluated with macro-F1/confusion matrix** | A, B, D (E partial) | Telegram via Telethon (14 auto-joined channels) | Python, Parquet | Mostly Telegram-only; auto-joining channels plus ML is the riskiest pattern under Telegram ToS |\[50\]
| 41 | Krushna-Sonar-04/sih_2026 (DRISHTI) | Analyst workspace plus grounded LLM assistant; aggregate-only demographics | A–E | X, Telegram (BotFather); simulated demo dataset | React/TS, FastAPI, PostgreSQL, VADER, NetworkX | VADER is English-lexicon and cannot handle Hinglish or sarcasm |\[51\]
| 42 | AdityaSarin1802/SocialMediaAnalysis | "Four-vector fusion" report | B, C, D, E | Mock data | Flask, lexicon sentiment, TF-IDF, NetworkX PageRank + greedy modularity | No real ingestion; lexicon sentiment |\[52\]
| 43 | vineetkush57-debug/Social-Media-Analytics | Full-stack SIH 2026 platform; public-figure analysis | B, D, E | Seeded SQLite demo | Vite + Python | Seeded data; profiling "public figures" invites SMCH-style criticism |\[53\]

**What "average" looks like (avoid it):** FastAPI + React dashboard; "IndicBERT/XLM-R" named but not evaluated (or VADER/lexicon used); TF-IDF/BERTopic trends; NetworkX PageRank/betweenness in a D3 force graph; Telethon or Bot API for Telegram; a seeded demo dataset; per-user demographic guesses; optional SHA-256 hash chain. Nearly all of them claim all five components and all six platforms. Few prove one component with numbers. We found no YouTube, LinkedIn or public Drive/PPT material in this pass, so the recon is GitHub-only.

### Coverage matrix
S = strong, W = weak/partial, — = absent/not evident. Columns: A–E; IN = Indian languages/Hinglish; TG = Telegram; SAR = sarcasm; CIB = coordination/bot detection; TS = temporal spread modelling; DPDP = privacy compliance; XAI = explainability; RT = real-time.

| Solution | A | B | C | D | E | IN | TG | SAR | CIB | TS | DPDP | XAI | RT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cyabra | S | W | W | S | S | W | S | — | S | W | — | W | S |
| Logically Intelligence | S | W | — | S | W | W (translation) | W | — | W | W | — | W | S |
| Graphika | W | — | — | W | S | — | W | — | S | W | — | S (analyst reports) | W |
| OSINT Monitor | S | S | — | S | — | — (Arabizi only) | — | — | — | — | — | — | S |
| Social Links | S | — | — | — | S | — | S | — | — | — | — | — | W |
| Meta Content Library | S (FB/IG) | — | — | W | — | — | — | — | — | — | W | — | W |
| Botometer X | — | — | — | — | — | — | — | — | W (archival) | — | — | W | — |
| Hoaxy2 / Coordiscope | W | — | — | W | S | — | — | — | W | S | — | W | W |
| Coordination Network Toolkit | — | — | — | — | S | — | — | — | S | W | — | S | — |
| M3 Inference | — | — | S (EU) | — | — | — | — | — | — | — | — | — | — |
| SentiMix top systems | — | S (3-class) | — | — | — | S | — | — | — | — | — | — | — |
| Hinglish sarcasm models | — | W | — | — | — | S | — | S (small data) | — | — | — | W | — |
| TwiBot-22 models | — | — | — | — | W | — | — | — | S (Twitter) | — | — | — | — |
| Pushshift/TGDataset | S (static) | — | — | — | W | — | S | — | — | W | — | — | — |
| SIH repo: Rudra "Sovereign" | S | W | W | W | W | W | S | W | W | W | — | — | W |
| SIH repo: NEXUS (×2) | S | W | W | S | W | W | W (Bot API) | W | W | W | W | S | W |
| SIH repo: Net-Sentinel | S | W | W | W | W | W | W | W | W | — | — | W (hash chain) | W |
| SIH repo: Krishna/Rishiraj | W | W | W (per-user, minors) | W | W | W | W | W | — | — | — | — | W |
| SIH repo: Traject | S | S (evaluated) | — | W | W | W | S | — | — | — | — | W | W |
| SIH repo: DRISHTI | W | W (VADER) | W (aggregate) | W | W | — | W | — | — | — | W | W | W |
| SIH repo: Sarin / vineetkush | — | W | W | W | W | — | — | — | — | — | — | — | — |
| Mainstream listening (unverified) | S | S | W | S | W | ? | ? | ? | — | — | ? | — | S |

### Empty cells → candidate gaps (with evidence)

1. **Evaluated Hinglish sarcasm and stance at the problem statement's granularity.** No benchmark matches "sarcasm/anxiety/excitement/supportive/against." SentiMix is 3-class, its best Hinglish system reached 75.0% weighted F1, and the top 15 teams all landed between 75% and 68.6% (Patwa et al., SemEval-2020). The Hinglish sarcasm corpus is about 5,000 tweets, 10% of them sarcastic.\[7\]\[54\] The 2026 Springer paper says augmentation "adds noise to code-mixed texts."\[10\] Competitors name models but, apart from Traject, publish no numbers.
2. **Valid Indian demographic inference.** M3's age F1 is 0.522 and swings from 0.28 to 0.73 by language, with multilingual validation on European languages.\[13\] Poststratification code exists only for EU census regions.\[15\] Repos output per-user age brackets, including under-18.\[48\]
3. **Bot detection after 2023.** Botometer X is archival (pre-June 2023) and cannot detect AI-enhanced bots, and its live endpoints shut down on 2 November 2026.\[38\]\[39\] TwiBot-22 shows detectors degrading as bots evolve.\[19\] No Telegram bot benchmark turned up in this research.
4. **Cross-platform temporal spread (Telegram↔X).** vera.ai names cross-platform coordination as a frontier, and ICWSM 2025 says alternative platforms "remain understudied."\[6\]\[24\] Pushshift shows Telegram forwarding is a first-class diffusion signal,\[55\] yet competitors draw static force graphs.
5. **Compliance-by-design.** Telegram API ToS 1.5 prohibits "using, accessing or aggregating data obtained from the Telegram platform to train, fine-tune or otherwise engage in the development… of artificial intelligence, machine learning models."\[56\] Its Content Licensing terms prohibit scraping for such purposes.\[57\] We found no competitor that addresses this. One even leaks credentials.\[43\]
6. **Calibrated, evidence-linked claims.** Research warns that coordination labels mean "coordinated behavior rather than verified inauthentic behavior," and TikTok CIB work reports many false-positive signals.\[4\]\[23\] Only NEXUS labels provenance;\[45\] nobody reports confidence or abstention.

### Practical reality in 2026

**Platform access**
- **X:** pay-per-use has been the default since 6 February 2026, with no free tier. A post read costs $0.005 and a user/follower read $0.010.\[58\] Legacy Basic ($200/month) accounts were migrated after 1 June 2026, and legacy Pro ($5,000/month) was deprecated with migration after 1 September 2026 (per Blotato).\[59\] Enterprise costs about $42,000+/month, and the default search window is 7 days.\[60\] **Conflict:** the monthly read cap is reported as 2M (Postproxy, Sorsa, SocialCrawl) or 3M (Blotato);\[59\]\[61\]\[62\]\[63\] check the developer console. At these prices, 10,000 posts cost about $50.
- **Telegram:** the Bot API only receives messages "from channels where they are a member,"\[44\] and channels generally add bots as admins, so it cannot monitor arbitrary public channels. MTProto clients (Telethon) need your own api_id, and their rate limits are undocumented FLOOD_WAIT errors.\[64\]\[65\] ToS 1.5 and the Content Licensing terms ban using Telegram data for AI/ML, and API access can be cut 10 days after notice.\[56\] **Implication:** use Telegram data for rule-based and graph analytics plus inference by models trained elsewhere, never for training. Say so on the Feasibility slide.
- **Instagram/Facebook:** Hashtag Search allows "a maximum of 30 unique hashtags… within a rolling, 7 day period" and requires App Review.\[66\] Business Discovery reads only professional accounts' metadata; consumer accounts are inaccessible.\[67\] The Meta Content Library is limited to vetted academics and non-profits.\[37\] Reports conflict on its follower threshold (100+, 1,000+ or 25,000+).\[37\]\[68\]\[69\]
- **Reddit:** free for non-commercial use at 100 queries per minute per OAuth client; commercial use costs $0.24 per 1,000 calls (secondary source).\[70\]
- **YouTube:** 10,000 units per day, free, and you cannot buy more.\[71\]\[72\] search.list costs 100 units and a commentThreads page costs 1 unit.\[73\]\[74\] Reportedly, since 1 June 2026 search has its own bucket (secondary source).\[75\] Comment ingestion is cheap; discovery is the constraint.

**Datasets for training and demo:** SentiMix Hinglish (about 20K), the Hinglish sarcasm corpora (about 5K; 427K unlabelled), Joshi 2016 Hinglish FB sentiment (3,879), HOT offensive (3,189), MaSaC (multimodal), TwiBot-22 (bots, graph), Pushshift Telegram (317M messages, to 2019) and TGDataset. For demographic calibration, M3 plus the poststratification method. Caution: using Pushshift/TGDataset to *train* may still conflict with the spirit of Telegram's terms, so use them for graph and diffusion evaluation.

**Legal/ethical**
- DPDP Act s.3(c)(ii) excludes personal data "made or caused to be made publicly available" by the data principal. The Act "does not expressly state that aggregation, enrichment, profiling, inference… removes" the exclusion (India Briefing).\[76\] In August 2024, however, the MeitY minister told the Rajya Sabha that scraping remains subject to the IT Act, the IT Rules and DPDP consent obligations.\[77\] That is legal ambiguity, so design conservatively.
- The DPDP Rules 2025 were notified in November 2025 (G.S.R. 846(E)). Sources differ on 13 vs 14 November. Commencement is phased, and there are heightened obligations for children's data (s.9 / Rule 10).\[78\]\[79\]\[80\]
- Recommended controls: keyed-HMAC pseudonymised author IDs (salted per deployment, rotated); no storage of profile images; no per-user demographic output, only aggregates; suppression of any cell with fewer than k accounts (for example k≥20); Laplace noise on published counts; explicit exclusion of predicted-minor accounts from analytics; retention limits; a tamper-evident audit log of every analyst query (not just of the data).

## Recommendations

**Positioning: "Compliance-first narrative forensics for India's code-mixed information space."** (Working names: *SUTRA* or *PRAHARI*.) The pitch to NTRO: *we detect when a narrative is being pushed, by whom (as clusters, not individuals), across Telegram and X, in Hinglish, with measured accuracy, without building a surveillance database.*

**Five USPs mapped to the evidence-backed gaps**
1. **Calibrated Hinglish affect with abstention (Gap 1).** Fine-tune MuRIL/XLM-R on SentiMix plus the sarcasm corpora; add stance and emotion heads; apply temperature scaling so the model returns "uncertain" instead of guessing. Put an **evaluation card** on the slide (macro-F1 per class, and against VADER as a baseline). Almost no competitor shows numbers.
2. **Coordination, not "bot scores" (Gaps 3, 6).** Port the Coordination Network Toolkit logic to Telegram: co-forward within Δt, near-duplicate text via MinHash, and shared-link bursts, alongside X co-retweet within 60 s.\[22\] Output "coordinated clusters" with evidence and confidence, following the literature's caution against calling them "inauthentic."\[4\]
3. **Cross-platform cascade lineage (Gap 4).** Link X posts and Telegram messages through URL, text fingerprint and time. Build a temporal graph of narrative jumps (first-seen per platform and community), with KOLs ranked by *time-to-amplification* rather than static PageRank. Keep NEXUS's honest "earliest observed" wording.\[45\]
4. **Privacy ledger by design (Gaps 2, 5).** Aggregate-only demographics (language via script and language ID; state-level geography from self-declared location; age *bands* reported only as poststratified aggregates with confidence intervals), k-suppression, differential-privacy noise, HMAC pseudonyms, no under-18 analytics. Telegram data is used for inference and graphs only, never training. This directly answers SMCH-style objections and Telegram ToS 1.5.
5. **Evidence-grade audit (the Blockchain & Cybersecurity theme, done right).** Use a Merkle-anchored log of *ingested data and analyst queries*. Net-Sentinel hashes data only;\[47\] auditing queries is the part that shows governance.

**Minimal viable architecture (fits the demo)**
Connectors: X pay-per-use (budget about $50 for 10K posts) + Telethon read-only on a curated list of public channels + YouTube comments + Reddit + replay of Pushshift/TGDataset → canonical schema (UTC, provenance tag LIVE/REPLAY/IMPORT) → Kafka/Redpanda-lite stream → NLP (language ID, transliteration normalisation, calibrated affect/stance/sarcasm) → BERTopic + burst detection → temporal multigraph (interaction + coordination layers) in Neo4j/NetworkX → privacy layer (k-suppression, DP) → analyst UI (evidence drawer, confidence, audit log).

**6-slide mapping**
1. **Title:** name, a tagline ("Narrative forensics, not surveillance"), team, PS ID.
2. **Proposed solution:** a problem vignette. Use the Meta-documented China-origin network posing as Indian journalists and activists and targeting Arunachal/Manipur discourse,\[81\] then show how A–E detect it.
3. **Technical approach:** the architecture above plus the evaluation card (Hinglish macro-F1, sarcasm F1, coordination precision on TwiBot-22 and seeded cascades).
4. **Feasibility & viability:** a platform access table with 2026 costs and limits; the Telegram ToS/DPDP compliance design; replay mode as fallback.
5. **Impact & benefits:** earlier warning on cross-border influence operations; fewer false accusations through calibrated abstention; auditable use (the SMCH lesson).
6. **Research & references:** SentiMix, M3, TwiBot-22, Coordination Network Toolkit, Pushshift Telegram, Meta threat report, Telegram ToS, DPDP s.3(c)(ii).

**Break-test checklist for your team:** Can you show a Hinglish sarcastic example handled correctly *and* one where the model abstains? Can you trace one narrative from a Telegram channel to X with timestamps? Can a judge query for a single individual's profile and be refused by design?

## Caveats
- Competitor recon covers public GitHub READMEs only. The READMEs describe claims, not verified working features, and there are likely many unpublished teams.
- X pricing figures come from third-party blogs citing X docs; the read cap (2M vs 3M) conflicts. The YouTube June 2026 bucket change and Reddit commercial pricing are also secondary.
- Mainstream social-listening products (Brandwatch, Talkwalker, Meltwater, Sprinklr, Pulsar), Maltego, Indian C-DOT/CDAC tools and state police labs were not verified in this pass. Their matrix cells are marked unverified.
- The reading of Telegram's ToS as covering research scraping is our interpretation of the published text, not a Telegram ruling. The DPDP treatment of inferences from public data is unsettled.
- NTRO's mandate details rely on secondary sources (Wikipedia), because NTRO publishes little officially.

## Sources

1. [From tweets to trends: analyzing sociolinguistic variation and change using the Twitter Corpus of English in Hong Kong (TCOEHK): Asian Englishes: Vol 27 , No 1 - Get Access](https://doi.org/10.1080/13488678.2023.2251771)
2. [National Technical Research Organisation](https://en.wikipedia.org/wiki/National_Technical_Research_Organisation)
3. [List of Indian intelligence agencies](https://en.wikipedia.org/wiki/List_of_Indian_intelligence_agencies)
4. [Optimal and heuristic strategies for evaluating the influence of coordinated behavior in information cascades and retweet networks](https://arxiv.org/html/2609.24398v1)
5. [Sahyog Portal - C4S Courses](https://c4scourses.in/national-affairs/sahyog-portal-2/)
6. [Coordinated Sharing Behavior Detection Conference at Sheffield](https://jerrygaolondon.substack.com/p/coordinated-sharing-behavior-detection)
7. [How Effective is Incongruity? Implications for Code-mix Sarcasm Detection](https://arxiv.org/pdf/2202.02702)
8. [“Did you really mean what you said?” : Sarcasm Detection in Hindi-English Code-Mixed Data using Bilingual Word Embeddings](https://arxiv.org/html/2010.00310)
9. [Sarcasm Detection in Hindi-Hinglish Code-Mixed Language: A Systematic Survey](https://www.researchgate.net/publication/399128056_Sarcasm_Detection_in_Hindi-Hinglish_Code-Mixed_Language_A_Systematic_Survey)
10. [Explainable Sarcasm Detection in Imbalanced Code-Mixed Text Using Focal Loss and Contextual Augmentation | Arabian Journal for Science and Engineering | Springer Nature Link](https://link.springer.com/article/10.1007/s13369-026-11298-8)
11. [Sarcasm Detection in Hindi-Hinglish Code-Mixed Language: A Systematic Survey | Springer Nature Link](https://link.springer.com/chapter/10.1007/978-981-95-0684-2_17)
12. [Elevating Code-mixed Text Handling through Auditory Information of Words](https://arxiv.org/pdf/2310.18155)
13. [Demographic Inference and Representative Population ...](https://arxiv.org/pdf/1905.05961)
14. [Demographic Inference and Representative Population Estimates from Multilingual Social Media Data \[Quick Review\]](https://liner.com/review/demographic-inference-and-representative-population-estimates-from-multilingual-social-media)
15. [GitHub - euagendas/twitter-poststratification: Poststratification code for "Demographic Inference and Representative Population Estimates from Multilingual Social Media Data" paper](https://github.com/euagendas/twitter-poststratification)
16. [Demographic inference and corrections for non-representativeness when working with multilingual social media data – GESIS Blog](https://blog.gesis.org/demographic-inference-and-corrections-for-non-representativeness-when-working-with-multilingual-social-media-data/)
17. [DADIT: A Dataset for Demographic Classification of Italian Twitter Users and a Comparison of Prediction Methods](https://arxiv.org/pdf/2403.05700)
18. [TwiBot-22: towards graph-based twitter bot detection](https://dl.acm.org/doi/10.5555/3600270.3602825)
19. [TwiBot-22: Towards Graph-Based Twitter Bot Detection \[Quick Review\]](https://liner.com/review/twibot22-towards-graphbased-twitter-bot-detection)
20. [BotMoE: Twitter Bot Detection with Community-Aware Mixtures of Modal-Specific Experts](https://arxiv.org/pdf/2304.06280)
21. [Social Media Bot Detection Research: Review of Literature](https://arxiv.org/pdf/2503.22838)
22. [s42001 024 00260 z](https://link.springer.com/article/10.1007/s42001-024-00260-z)
23. [Coordinated Inauthentic Behavior on TikTok: Challenges and Opportunities for Detection in a Video-First Ecosystem](https://arxiv.org/pdf/2505.10867)
24. [Investigating Coordinated Inauthentic Behavior on Alternative Platforms During](https://workshop-proceedings.icwsm.org/pdf/2025_19.pdf)
25. [Coordinated Sharing Behavior Detection (Conference): Report and Insights – vera.ai VERification Assisted by Artificial Intelligence](https://www.veraai.eu/posts/coordinated-sharing-behavior-detection-conference-2024)
26. [\[2001.08438\] The Pushshift Telegram Dataset](https://www.arxiv-vanity.com/papers/2001.08438/)
27. [TGDataset: Collecting and Exploring the Largest Telegram Channels Dataset](https://arxiv.org/pdf/2303.05345)
28. [Cyabra Platform: Uncover The Good, Bad and Fake Online](https://www.britopian.com/business-directory/cyabra/)
29. [Public Safety - Cyabra](https://cyabra.com/solutions/public-safety/)
30. [Social Media Threat Monitoring for Security Teams - Cyabra](https://cyabra.com/solutions/security-cyber/)
31. [Narrative Intelligence - Cyabra](https://cyabra.com/glossary/narrative-intelligence/)
32. [Cyabra Reviews & Ratings 2026 | Gartner Peer Insights](https://www.gartner.com/reviews/product/cyabra-1283790865)
33. [Best Cyabra Alternatives & Competitors](https://sourceforge.net/software/product/Cyabra/alternatives)
34. [Welcome to OSINTMon](https://www.osintmon.com/)
35. [OSINT & Social Media Intelligence Investigation Solutions](https://sociallinks.io/)
36. [Researchers Consider the Impact of Meta's CrowdTangle Shutdown | TechPolicy.Press](https://www.techpolicy.press/researchers-consider-the-impact-of-metas-crowdtangle-shutdown/)
37. [Meta Content Library | Bellingcat's Online Investigation Toolkit](https://bellingcat.gitbook.io/toolkit/more/all-tools/meta-content-library)
38. [Botometer Pro](https://rapidapi.com/OSoMe/api/botometer-pro)
39. [Introducing Botometer X](https://osome.iu.edu/research/blog/introducing-botometer-x)
40. [Exploring the Latest OSoMe Tools](https://osome.iu.edu/research/blog/exploring-the-latest-osome-tools)
41. [NDCRTC](https://en.wikipedia.org/wiki/NDCRTC)
42. [Proposal of "Social Media Communication Hub" withdrawn by Centre: AG KK Venugopal | SCC Times](https://www.scconline.com/blog/post/2018/08/03/proposal-of-social-media-hub-withdrawn-by-centre-ag-kk-venugopal/)
43. [GitHub - RudraSuthar-web/SIH26152-Social-Media-Analysis · GitHub](https://github.com/RudraSuthar-web/SIH26152-Social-Media-Analysis)
44. [Bots FAQ](https://core.telegram.org/bots/faq)
45. [GitHub - omghotekar01-dotcom/SOCIAL-MEDIA---PS152 · GitHub](https://github.com/omghotekar01-dotcom/SOCIAL-MEDIA---PS152)
46. [GitHub - Shubham2025-ai/NEXUS\_SIH26152\_FULL\_PROJECT: NEXUS — Narrative & Influence Intelligence (SIH26152)](https://github.com/Shubham2025-ai/NEXUS_SIH26152_FULL_PROJECT)
47. [GitHub - MrManasss/net-sentinel-social: AI-driven social media intelligence and counter-disinformation framework featuring nuanced NLP sentiment, demographic profiling, trend momentum, network topology, and SHA-256 cryptographic audit logs. Built for SIH 2026 (Problem Statement SIH26152). · GitHub](https://github.com/MrManasss/net-sentinel-social)
48. [GitHub - Krishna-Das20/SIH-26152 · GitHub](https://github.com/Krishna-Das20/SIH-26152)
49. [GitHub - Rishiraj-De/SIH-26152 · GitHub](https://github.com/Rishiraj-De/SIH-26152)
50. [GitHub - singharyan-912/Traject · GitHub](https://github.com/singharyan-912/Traject)
51. [GitHub - Krushna-Sonar-04/sih\_2026 · GitHub](https://github.com/Krushna-Sonar-04/sih_2026)
52. [GitHub - AdityaSarin1802/SocialMediaAnalysis · GitHub](https://github.com/AdityaSarin1802/SocialMediaAnalysis)
53. [GitHub - vineetkush57-debug/Social-Media-Analytics: AI-powered platform for social media trend, sentiment, engagement, and public-figure analysis. · GitHub](https://github.com/vineetkush57-debug/Social-Media-Analytics)
54. [\[2010.00310\] “Did you really mean what you said?” : Sarcasm Detection in Hindi-English Code-Mixed Data using Bilingual Word Embeddings](https://ar5iv.labs.arxiv.org/html/2010.00310)
55. [The Pushshift Telegram Dataset](https://arxiv.org/pdf/2001.08438)
56. [Telegram API Terms of Service](https://core.telegram.org/api/terms)
57. [Terms of Service for Content Licensing](https://telegram.org/tos/content-licensing)
58. [X API Pricing 2026: Pay-Per-Use Rates and What a Post Costs](https://www.postzen.dev/blog/twitter-api-pricing)
59. [X (Twitter) API Pricing: Complete Guide for 2026 - Blotato](https://www.blotato.com/blog/twitter-api-pricing)
60. [Twitter API Pricing 2026: Pay-Per-Use Costs & Alternatives | Xpoz Blog](https://www.xpoz.ai/blog/guides/understanding-twitter-api-pricing-tiers-and-alternatives/)
61. [X (Twitter) API Pricing in 2026: All Tiers | Postproxy](https://postproxy.dev/blog/x-api-pricing-2026/)
62. [X (Twitter) API in 2026: Credit Pricing + 3 Cheaper Routes | SocialCrawl](https://www.socialcrawl.dev/blog/x-twitter-api-2026)
63. [X (Twitter) API Pricing 2026: Tiers, Free Tier & Real Costs](https://api.sorsa.io/blog/twitter-api-pricing-2026)
64. [Creating your Telegram Application](https://core.telegram.org/api/obtaining_api_id)
65. [Telethon vs Telegram Bot API for Outreach (Technical Guide)](https://zupai.io/blog/telethon-vs-telegram-bot-api-for-outreach)
66. <https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/hashtag-search/>
67. [Facebook\_Instagram-API/Instagram API Documentation.md · main · Hackathon 2024 / Retrieval modules / Platform Docs Versions · GitLab](https://code.peren.gouv.fr/hackathon-2024/retrieval-modules/platform-docs-versions/-/blob/main/Facebook_Instagram-API/Instagram%20API%20Documentation.md)
68. [Meta Content Library and API | Transparency Center](https://transparency.meta.com/researchtools/meta-content-library)
69. [Updates to Meta Content Library and API in Support of Independent Research | Transparency Center](https://transparency.meta.com/researchtools/meta-content-library/MCL-API-update-supporting-independent-research/)
70. [Reddit API in 2026: Pricing, Rate Limits & What Works | SocialCrawl](https://www.socialcrawl.dev/blog/reddit-data-api-2026)
71. [YouTube API Free in 2026? Quota Limits & Costs](https://www.getphyllo.com/post/is-the-youtube-api-free-in-2026-quota-limits-costs-when-to-pay)
72. [YouTube API Pricing in 2026: Is It Free? What It Actually Costs | OutlierKit Resources](https://outlierkit.com/resources/youtube-api-pricing/)
73. [YouTube API Quota: 100 Searches Burn 10,000 Units (2026) | SocialCrawl](https://www.socialcrawl.dev/blog/youtube-data-api-2026)
74. [Batch Processing & Quota Management](https://cran.nics.utk.edu/cran/web/packages/tuber/vignettes/batch-processing-quota.html)
75. [YouTube API Pricing: Complete Guide for 2026 - Blotato](https://www.blotato.com/blog/youtube-api-pricing)
76. [DPDP Act: Can Companies Use Publicly Available Personal Data?](https://www.india-briefing.com/news/india-dpdp-act-publicly-available-personal-data-46899.html)
77. [Publicly Available Data under the DPDP Act: The Limits of Exemptions in AI-Driven Processing](https://lawschoolpolicyreview.com/2026/01/13/publicly-available-data-under-the-dpdp-act-the-limits-of-exemptions-in-ai-driven-processing/)
78. [DPDP Rules 2025: India’s Complete Compliance Guide | Seclore](https://www.seclore.com/fundamentals/dpdp-rules-2025-compliance-guide/)
79. [DPDP Rules, 2025 Notified](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190655&reg=48&lang=2)
80. [DPDP Rules 2025: Requirements & Timeline](https://institute.privacytru.com/resources/dpdp-rules-2025)
81. <https://transparency.meta.com/sr/Q3-2023-Adversarial-threat-report/>
