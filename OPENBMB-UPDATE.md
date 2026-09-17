# OpenBMB follow-up draft — not sent

Thanks for encouraging me to polish the project. I now have a portable,
MIT-licensed research preview of MiniCPM News Desk ready for review.

The idea is practical: help people keep up with official AI and technology news
when they have limited reading time. MiniCPM5-2B runs locally on an existing
CPU-only Linux desktop and selects source passages explaining what changed and
how it can be used. The report retains source links and relevant access, pricing
and setup conditions so readers can dig deeper.

The code now includes 110 offline tests, a no-model quick start and clearly labeled
normal/fallback examples. I also ran the actual guarded CLI on the Linux machine
with three fresh model requests: all three passed source-based content review,
including two repetitions of a case that previously returned no highlights.
Each took about 59–61 seconds including setup and cleanup. Local provider API cost
was $0; I am not claiming measured total cost savings.

I have kept the limitations visible. An earlier eight-request run passed7/8
content checks. If the model selects nothing, the application shows the full
original source with a fallback label rather than pretending it generated a good
summary. This is still a review-required prototype, not an unattended news service.

I started with my own AI/tech workflow. The approach could be adapted to other
topics, but those have not been evaluated yet. The package includes the measured
results and failure history alongside setup/security guidance.

Public repository: https://github.com/fenner888/minicpm-news-desk

I would welcome your team's feedback on the MiniCPM runtime configuration and
this practical local-inference use case as the research preview develops.
