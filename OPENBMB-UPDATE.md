# OpenBMB follow-up draft — not sent (updated September18)

Thanks for encouraging me to polish the project. I now have a portable,
MIT-licensed research preview of MiniCPM News Desk ready for review.

The idea is practical: help people keep up with official AI and technology news
when they have limited reading time. MiniCPM5-2B runs locally on an existing
CPU-only Linux desktop and selects source passages explaining what changed and
how it can be used. The report retains source links and relevant access, pricing
and setup conditions so readers can dig deeper.

The project now centers on one daily recap of the previous24 hours: a lead story,
other updates worth knowing, and source-linked quick hits. Collection can run
hourly without hourly MiniCPM notifications. Dates, deduplication, budgets and
delivery receipts are deterministic code; the model selects grounded passages.

The public package includes166 offline tests and a fictional no-model daily demo.
The separate private integration passes237 tests in total. The editorial update
replayed three saved real-model results into two Telegram messages, with full
extracted articles and placement decisions retained in a private supporting report.
This presentation test made no new model calls. The first scheduled daily delivery
is still pending; shorter source-extractive writing still needs reader review.

Earlier on September18, three real GitHub article tests each produced useful
local selections in roughly40–43 seconds including setup/checks/cleanup. Those
are development observations, not a general accuracy estimate. Local provider
API cost was $0; I am not claiming measured total cost savings.

I have kept the limitations visible. An earlier eight-request run passed7/8
content checks. If the model selects nothing, the application shows the full
original source with a fallback label rather than pretending it generated a good
summary. This is still a review-required research preview. The owner-authorized
private daily integration is separate from the portable public package, and its
ongoing usefulness and delivery reliability still need observation.

I started with my own AI/tech workflow. The approach could be adapted to other
topics, but those have not been evaluated yet. The package includes the measured
results and failure history alongside setup/security guidance.

Public repository: https://github.com/fenner888/minicpm-news-desk

I would welcome your team's feedback on the MiniCPM runtime configuration and
this practical local-inference use case as the research preview develops.
