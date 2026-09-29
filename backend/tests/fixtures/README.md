# Golden fixtures

Payloads here are **constructed from each library's documented field names**
(twscrape 0.20 `Tweet.json()`, Telethon `Message`, PRAW `Comment`, YouTube Data
API v3 `commentThreads.list`, Meta/CrowdTangle CSV export). They are not
recordings of live traffic: capturing real recordings needs platform
credentials (PRD section 20). When credentials are available, record real
payloads with `scripts/check_collectors.py --record` and add them here.
