# PRAHARI: diagrams (Mermaid) and references

Paste each block into https://mermaid.live (or any Mermaid renderer) to export PNG/SVG for slides.

---

## 1. System architecture

```mermaid
flowchart LR
    subgraph SRC["A · Data sources"]
        X["X / Twitter<br/>(twscrape)"]
        TG["Telegram<br/>(Telethon)"]
        RD["Reddit<br/>(PRAW)"]
        YT["YouTube<br/>(Data API v3)"]
        IGFB["Instagram / Facebook<br/>(export CSV import)"]
        RP["Replay<br/>(synthetic scenario)"]
    end

    subgraph ING["Ingestion (resilient)"]
        COL["Collectors<br/>backoff · circuit breaker · health"]
        NORM["Normaliser<br/>canonical Post / Account / Edge / Media"]
    end

    subgraph LED["Theme · Evidence ledger (Blockchain & Cybersecurity)"]
        CH["SHA-256 hash chain<br/>append-only raw_records"]
        MK["Merkle checkpoints<br/>every 100 records"]
        SG["Ed25519 signatures"]
        OTS["OpenTimestamps<br/>Bitcoin anchoring"]
    end

    DB[("SQLite WAL + FTS5<br/>posts · accounts · edges · media")]

    subgraph AN["Analytics engine"]
        B["B · Emotion<br/>mDeBERTa NLI + XLM-R"]
        C["C · Demographics<br/>k-anonymity + DP noise"]
        D["D · Trends<br/>topics · Kleinberg bursts ·<br/>rise score · GBR + Hawkes forecast"]
        E["E · Network<br/>cascade KOLs · bridges · spread"]
        V2["Coordination detector<br/>narrative clusters · per-account"]
        V3["Lineage<br/>earliest observed · pHash"]
        SC["Signal Cards<br/>priority + why fired"]
    end

    subgraph OUT["Analyst console (React)"]
        UI["1 Situation Room →<br/>2 Detect: Platforms · Trends · Emotions →<br/>3 Investigate: Coordination · Network · Lineage · Audience →<br/>4 Evidence: Cases · Ledger"]
        CASE["Case brief +<br/>draft BSA §63 certificate"]
        LLM["Gemini summaries<br/>(injection-safe)"]
    end

    API["FastAPI<br/>REST + SSE"]

    X & TG & RD & YT & IGFB & RP --> COL --> CH
    CH --> MK --> SG --> OTS
    CH --> NORM --> DB
    DB --> B & C & D & E & V2 & V3
    V2 -. "organic-only filter" .-> B & C & D & E
    B & D & V2 --> SC
    SC & V3 & C & E --> API
    DB --> API
    API --> UI --> CASE
    API --> LLM
    SG -. "verify · inclusion proofs · tamper sim" .-> UI
```

---

## 2. Workflow diagram

```mermaid
flowchart TD
    S([Start]) --> COLLECT["Collect posts, replies, forwards<br/>X · Telegram · Reddit · YouTube · IG/FB import"]
    COLLECT --> HASH["Canonical JSON → SHA-256<br/>chain into append-only ledger"]
    HASH --> CP{"100 records?"}
    CP -- yes --> SIGN["Merkle root + Ed25519 signature<br/>→ OpenTimestamps anchor"]
    CP -- no --> NORM
    SIGN --> NORM["Normalise → canonical posts,<br/>accounts, interaction edges, media pHash"]
    NORM --> EMO["Score emotions<br/>anxiety · excitement · sarcasm ·<br/>supportive · against"]
    EMO --> TOP["Cluster topics per 24 h window<br/>+ centroid matching"]
    TOP --> COORD["Detect coordination<br/>narrative clusters → per-account scores"]
    COORD --> SPLIT{"Account score ≥ 0.7?"}
    SPLIT -- yes --> COORDSET["Mark as coordinated"]
    SPLIT -- no --> ORG["Organic"]
    COORDSET & ORG --> VIEWS["Compute every view twice:<br/>RAW and ORGANIC-ONLY"]
    VIEWS --> TR["Trends: Kleinberg bursts,<br/>rise score, forecasts"]
    VIEWS --> DEM["Demographics:<br/>cohorts, k=10, Laplace noise"]
    VIEWS --> NET["Network: KOLs, bridges,<br/>spread over time"]
    VIEWS --> LIN["Lineage: earliest observed platform,<br/>repost chains, image variants"]
    TR & NET & LIN --> ALERT{"Burst + coordination<br/>+ anxiety shift + reach"}
    ALERT -- "priority ≥ 70" --> CARD["High-priority Signal Card<br/>with 'why fired' evidence"]
    ALERT -- "< 70" --> WATCH["Low-priority / watch list"]
    CARD --> ANALYST["Analyst reviews in console<br/>raw vs organic toggle"]
    DEM --> ANALYST
    ANALYST --> CASE["Open case → brief with evidence index<br/>(ledger seq + hashes) + draft §63 certificate"]
    CASE --> VERIFY["Anyone verifies with public key:<br/>hash chain · Merkle root · signature · Bitcoin"]
    VERIFY --> E([Evidence handed over])
```

---

## 3. Impact square

Qualitative positioning of what PRAHARI changes, by who benefits (x-axis) and how
direct the effect is (y-axis). Placement is a judgement, not a measurement; the
measured numbers are in `eval/reports/summary.json`.

```mermaid
quadrantChart
    title PRAHARI impact square
    x-axis Operational - analyst team --> Societal - public and institutions
    y-axis Indirect benefit --> Direct benefit
    quadrant-1 Public safety and trust
    quadrant-2 Analyst productivity
    quadrant-3 Capability building
    quadrant-4 Governance and rights
    Fewer, explained alerts: [0.18, 0.86]
    Early rumour warning: [0.62, 0.9]
    Organic vs coordinated view: [0.4, 0.78]
    Cross-platform origin tracing: [0.3, 0.66]
    Court-ready evidence ledger: [0.78, 0.72]
    Privacy-preserving demographics: [0.84, 0.36]
    Multilingual Indic NLP base: [0.22, 0.3]
    Open, auditable methods: [0.66, 0.22]
```

Alternative 2×2 box version (if your slide template needs text boxes):

```mermaid
flowchart TB
    subgraph R1[" "]
        direction LR
        Q2["<b>Analyst productivity</b><br/>0.14 vs 35 high-priority alerts/day<br/>one-click case brief<br/>raw vs organic toggle"]
        Q1["<b>Public safety</b><br/>rumour flagged 5 min before a volume alarm<br/>origin traced: Telegram → X in 12 min<br/>coordinated amplification exposed"]
    end
    subgraph R2[" "]
        direction LR
        Q3["<b>Capability building</b><br/>Hinglish / Indic NLP pipeline<br/>reusable collectors + eval harness<br/>path to MuRIL fine-tune"]
        Q4["<b>Governance & rights</b><br/>tamper-evident evidence (1000/1000 caught)<br/>k-anonymity + differential privacy<br/>no individual profiling"]
    end
    R1 --- R2
```

---

## 4. References (plain text, with links for verification)

Algorithms and methods
1. J. Kleinberg, "Bursty and Hierarchical Structure in Streams," Proc. ACM SIGKDD, 2002. https://doi.org/10.1145/775047.775061
2. K.-I. Goh and A.-L. Barabási, "Burstiness and memory in complex systems," EPL 81, 48002, 2008. https://doi.org/10.1209/0295-5075/81/48002 (preprint: https://arxiv.org/abs/physics/0610233)
3. A. G. Hawkes, "Spectra of some self-exciting and mutually exciting point processes," Biometrika 58(1), 83–90, 1971. https://doi.org/10.1093/biomet/58.1.83
4. D. Pacheco et al., "Uncovering Coordinated Networks on Social Media: Methods and Case Studies," ICWSM 2021. https://doi.org/10.1609/icwsm.v15i1.18075
5. F. B. Keller, D. Schoch, S. Stier, J. Yang, "Political Astroturfing on Twitter: How to Coordinate a Disinformation Campaign," Political Communication 37(2), 2020. https://doi.org/10.1080/10584609.2019.1661888
6. L. Page, S. Brin, R. Motwani, T. Winograd, "The PageRank Citation Ranking: Bringing Order to the Web," Stanford InfoLab, 1999. http://ilpubs.stanford.edu:8090/422/
7. U. Brandes, "A faster algorithm for betweenness centrality," Journal of Mathematical Sociology 25(2), 2001. https://doi.org/10.1080/0022250X.2001.9990249
8. A. Clauset, M. E. J. Newman, C. Moore, "Finding community structure in very large networks," Physical Review E 70, 066111, 2004. https://doi.org/10.1103/PhysRevE.70.066111
9. C. Zauner, "Implementation and Benchmarking of Perceptual Image Hash Functions," MSc thesis, 2010. https://www.phash.org/docs/pubs/thesis_zauner.pdf

NLP models
10. P. He, J. Gao, W. Chen, "DeBERTaV3: Improving DeBERTa using ELECTRA-Style Pre-Training with Gradient-Disentangled Embedding Sharing," 2021. https://arxiv.org/abs/2111.09543 — model used: https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-mnli-xnli
11. A. Conneau et al., "XNLI: Evaluating Cross-lingual Sentence Representations," EMNLP 2018. https://arxiv.org/abs/1809.05053
12. W. Yin, J. Hay, D. Roth, "Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach," EMNLP 2019. https://arxiv.org/abs/1909.00161
13. A. Conneau et al., "Unsupervised Cross-lingual Representation Learning at Scale" (XLM-R), ACL 2020. https://arxiv.org/abs/1911.02116
14. F. Barbieri, L. Espinosa Anke, J. Camacho-Collados, "XLM-T: Multilingual Language Models in Twitter for Sentiment Analysis and Beyond," LREC 2022. https://arxiv.org/abs/2104.12250 — model used: https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment
15. N. Reimers, I. Gurevych, "Sentence-BERT," EMNLP 2019. https://arxiv.org/abs/1908.10084
16. N. Reimers, I. Gurevych, "Making Monolingual Sentence Embeddings Multilingual using Knowledge Distillation," EMNLP 2020. https://arxiv.org/abs/2004.09813 — model used: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
17. S. Khanuja et al., "MuRIL: Multilingual Representations for Indian Languages," 2021 (planned fine-tune). https://arxiv.org/abs/2103.10730

Cryptography, evidence and privacy
18. R. C. Merkle, "A Digital Signature Based on a Conventional Encryption Function," CRYPTO '87. https://doi.org/10.1007/3-540-48184-2_32
19. D. J. Bernstein et al., "High-speed high-security signatures" (Ed25519), Journal of Cryptographic Engineering, 2012. https://doi.org/10.1007/s13389-012-0027-1
20. S. Josefsson, I. Liusvaara, "Edwards-Curve Digital Signature Algorithm (EdDSA)," RFC 8032, 2017. https://www.rfc-editor.org/rfc/rfc8032
21. A. Rundgren, B. Jordan, S. Erdtman, "JSON Canonicalization Scheme (JCS)," RFC 8785, 2020. https://www.rfc-editor.org/rfc/rfc8785
22. OpenTimestamps (Bitcoin-anchored timestamping). https://opentimestamps.org
23. L. Sweeney, "k-anonymity: A model for protecting privacy," Int. J. Uncertainty, Fuzziness and Knowledge-Based Systems 10(5), 2002. https://doi.org/10.1142/S0218488502001648
24. C. Dwork, F. McSherry, K. Nissim, A. Smith, "Calibrating Noise to Sensitivity in Private Data Analysis," TCC 2006. https://doi.org/10.1007/11681878_14
25. Bharatiya Sakshya Adhiniyam, 2023 (Act No. 47 of 2023), Section 63 — electronic records. Official text: India Code, https://www.indiacode.nic.in (search "Bharatiya Sakshya Adhiniyam").

Software
26. F. Pedregosa et al., "Scikit-learn: Machine Learning in Python," JMLR 12, 2011. https://jmlr.org/papers/v12/pedregosa11a.html
27. A. Hagberg, D. Schult, P. Swart, "Exploring Network Structure, Dynamics, and Function using NetworkX," SciPy 2008. https://conference.scipy.org/proceedings/SciPy2008/paper_2/
28. Hugging Face Transformers (T. Wolf et al., EMNLP 2020 demos). https://arxiv.org/abs/1910.03771
