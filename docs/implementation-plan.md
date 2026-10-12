# Implementation plan

The proof of concept: the real system with simulated partners, serving two purposes at
once — an engineering artifact that demonstrates the hard invariants, and a behavioural
experiment that answers whether groups actually keep deciding.

## What "done" means

Four invariants demonstrable by test:

1. A decision fans out to 50 member accounts in under 30 seconds, each sized and
   consented individually.
2. Everyone in a batch receives the same average price, with the allocation recorded
   before the order is submitted.
3. Replay, duplicate callbacks, partial fills and ambiguous timeouts never produce a
   duplicate order.
4. Injected position drift freezes the affected account within one reconciliation cycle.

Plus one behavioural answer: **do 30–40 real friend groups still propose and vote in
week eight?**

## Milestones

| Milestone | Weeks | Ships |
| --- | --- | --- |
| **M0 Foundations** | 1 | Repo, module skeleton, schema per module, `Money`/`Weight` with float rejection, property tests, CI, import-boundary lint, OpenTelemetry |
| **M1 Decision engine** | 2–3 | Guild and Proposal aggregates, ballots, frozen electorate and rules, strategy versions with compare-and-set, outbox + publisher |
| **M2 Fan-out and consent** | 4–5 | `MemberRebalance`, per-member sizing and netting, limit enforcement, consent capture, expiry, skip reasons |
| **M3 Execution and allocation** | 6–7 | Batching window, sealed allocation statement, block submission, average-price allocation, pro-rata partials, idempotency keys |
| **M4 Simulator and chaos** | 8 | Adapter protocol, config-driven chaos, the suite proving invariants 1–3 |
| **M5 Ledger and reconciliation** | 9–10 | Sub-ledger projections, three-way reconciliation, break detection and freeze, statements |
| **M6 Frontend** | 11–13 | Eight critical-path screens: Guild list, Guild home, proposal and ballot, create proposal, consent card, rebalance status, position receipt, skip explainer |
| **M7 Agent layer** | 14–15 | LangGraph service: draft, explain, monitor. Eval harness with golden cases in CI, member-scoped retrieval |
| **M8 Publish and pilot** | 16 | README, demo script, trace walkthrough, deploy, groups invited |

**Calibration:** roughly 16 focused weeks. Alongside a full-time job, assume double.

**The fork at M5.** If behavioural evidence matters more than reconciliation depth —
and for fundraising it does — swap M6 ahead of M5. A thin UI over M1–M4 is enough to
run the pilot, and the pilot takes eight weeks of calendar time regardless. Starting it
at week 11 instead of week 16 is five weeks of evidence that cannot be bought back.

## The pilot

Eight weeks from whenever the UI lands. Paper portfolios, real groups, real arguments.

- **Recruit** 30–40 groups: classmates, teams, existing finance chats. Concierge
  onboarding, by hand.
- **Measure:** decisions per Guild per month, consent conversion, proportion of Guilds
  still deciding in week eight, skip reasons by code, time from invite accepted to first
  rebalance.
- **The number that matters:** week-eight survival. Everything else is secondary.

## Deliberately not building

Real partners, money movement, identity verification beyond magic links, crypto, cards,
mobile apps, Mirror and copy trading, leagues, badges, rewards, Pacts. Each is
defensible later; none tests the hypothesis.

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope creep into production shapes (Kafka, Kubernetes, Terraform) | Postgres and Docker Compose until the pilot ends |
| Simulator divergence from real partner semantics | Write it from a real partner's API documentation, not from imagination |
| Pilot attrition in week three | Recruit enough groups that attrition still leaves a signal |
| Solo bandwidth | The frontend is the compressible part; the invariant work is not |
