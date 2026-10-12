# Architecture decisions

Each record states the decision, the alternative rejected, and the consequence we
accepted. A decision without a named cost is not a decision.

| # | Decision | Rejected | Consequence |
| --- | --- | --- | --- |
| [0001](0001-partners-are-the-system-of-record.md) | Partners hold the system of record; we keep an event-sourced projection | Our ledger as truth | Reconciliation becomes a first-class service and a release gate |
| [0002](0002-modular-monolith-first.md) | Modular monolith with enforced import boundaries | Microservices from day one | Extraction deferred; boundaries must be policed in CI |
| [0003](0003-batched-orders-with-sealed-allocation.md) | Batched orders with a pre-trade allocation statement | Per-account sequential orders | Consent collects into a window, so some members wait |
| [0004](0004-account-per-guild.md) | One brokerage account per member per Guild | One account with ledger-side tagging | ~1.5× account count and cost |
| [0005](0005-agents-off-the-order-path.md) | Agents never compute a number that reaches an order | Agent-computed sizing | Deterministic execution; the agent explains rather than decides |
| [0006](0006-decimal-money-basis-point-weights.md) | `Decimal` money, integer basis-point weights, floats rejected | Floats with rounding at the edges | Discipline enforced by types and lint instead of a compiler |
| 0007 | Transactional outbox with a polling publisher (PoC) | Dual writes; CDC at PoC scale | Consumers must be idempotent; ordering is per aggregate only |
| 0008 | Python for the PoC; the money path may move to Kotlin later | All-Kotlin, or all-Python forever | Weaker money and concurrency guarantees, bought for speed and AI ecosystem |
