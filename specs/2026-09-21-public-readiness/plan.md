# Public readiness plan

Owner: Mark. User approved the September 21 audit remediation recommendation.
Baseline: public 0.7.5, commit 9b38dd7cefac0e3117f0233e1218842acd539212.

Five flows: initialize/collect; build and inspect; explicitly send; inspect/recover
state; optionally schedule commands after manual acceptance. First reproduce the
two source-preservation defects with failing tests; then implement and review.

Data: public announcements; private local source/model archives; Telegram token
and numeric destination only in operator environment, never model context or Git.
No payments, health data, minors' data, account system or public uploads.

Implement in this public checkout only. Preserve historical fixtures and evidence.
Do not change Cheryl's services, production state or credentials. Do not install a
schedule. Live inference, delivery and Git publication require their own explicit
acceptance checkpoint; offline/mock evidence does not substitute for them.
