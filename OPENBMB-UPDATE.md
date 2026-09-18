# OpenBMB follow-up draft — not sent

Updated September 18, 2026. This is a project update draft, not evidence of
selection, endorsement, an award or a submitted follow-up.

I've made MiniCPM News Desk public as an MIT-licensed research preview.

I wanted to test a practical use for MiniCPM5-2B on hardware I already own:
an Intel Core i5-9400F Linux desktop with 16 GB RAM, using CPU-only inference.
The project helps me keep up with official AI and technology announcements
when I don't have time to read every article in depth.

The private workflow collects hourly and is configured for one 8 AM Eastern
recap of the preceding 24 hours. MiniCPM selects useful passages from supported
articles. Code handles dates, deduplication, source qualifications, formatting
and delivery. Quick hits use labeled publisher excerpts or headline links;
those are separate from full-article model-derived briefs.

The latest real test used version 0.7.4. One fresh local request completed in
40.57 seconds, and the recap reached Telegram in two confirmed parts: one model
brief plus eight source-only items. An initial manual launch-path error required
correction before that run. We also found and repaired an earlier omission of
migration dates and version-pinning guidance. The failure history remains visible
in EVALUATION.md; this is not a general accuracy or unattended-reliability claim.

The public package is now 0.7.5, with 203 offline tests and an additional
conservative reading-view fix for qualifications embedded in navigation-like
passages. That formatter change has not been deployed or fresh-model tested.
The private integration remains separate; its first scheduled morning delivery
still needs observation. The public repository does not install a collector,
connect Telegram or configure an unattended job for someone cloning it.

I see this as a practical local-inference/deployment experiment. Provider API
charges for these local runs were zero, but electricity, hardware and review
time are not free; I haven't measured savings against a hosted baseline.

The approach could be adapted to other subjects, although I've only evaluated
these AI/tech development examples so far. The public package includes setup
instructions, synthetic demos, tests, known limitations and the evaluation record.

Repository: https://github.com/fenner888/minicpm-news-desk

I'd welcome feedback on the runtime configuration and where to improve this
small-model use case next.
