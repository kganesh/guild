# Architecture

This is the condensed, repository-resident version of the engineering architecture.
It covers what a contributor needs to work in this codebase: the constraints, the
shape of the system, and the rules that are not negotiable.

## 1. The binding constraint

Guild does not hold money, securities or accounts. Partners do:

| Capability | System of record |
| --- | --- |
| Brokerage accounts, positions, cash, executions | Clearing firm |
| Deposit accounts, transfers, card | Sponsor bank |
| Identity verification, sanctions screening | Identity vendor |

Our ledger is therefore a **projection** of data owned elsewhere. Correctness means
continuous agreement with someone else's records, not internal consistency with our
own database. Every design decision below follows from that.

In the proof of concept all of these are **simulated** behind the same adapter
interface a real partner would implement.

## 2. Shape of the system

```
clients ──► API (FastAPI)
              │
              ▼
        domain packages ──► outbox table ──► publisher ──► consumers
         guild · trading                                      │
         ledger · recon                                       ▼
              │                                          projections
              ▼
        partner adapters ──► clearing / bank (simulated)
                                    │
                                    ▼
                             position + cash files
                                    │
                                    ▼
                            reconciliation service
```

**Modular monolith, not microservices.** One deployable, one package per bounded
context, import boundaries enforced in CI. The boundaries are drawn where services
would be split later, so extraction is mechanical rather than a rewrite.

## 3. Bounded contexts

| Context | Owns | Type |
| --- | --- | --- |
| `guild` | Guilds, membership, governance, proposals, ballots, strategy versions, rebalances | Core |
| `trading` | Order intents, batching, allocation, fills | Supporting |
| `ledger` | Sub-ledger, balances, protection labels, statements | Supporting |
| `recon` | Three-way reconciliation, break detection, account freeze | Supporting |
| `adapters/partners` | One adapter per external provider | Anti-corruption layer |
| `agents` | Drafting, explanation, monitoring | Supporting, off the order path |

## 4. The critical path

```
decision closes
  └─ Proposal.decide()            — one transaction, state + outbox event
     └─ StrategyVersion published  — compare-and-set on version number
        └─ fan-out                 — one MemberRebalance per member, independent
           └─ eligibility + limits — member's own policy applied
              └─ consent           — explicit tap, or auto-follow authorisation
                 └─ batching window — consents collect
                    └─ allocation statement — written and sealed BEFORE submission
                       └─ block order       — one order, idempotency key
                          └─ fills          — average price allocated to all accounts
                             └─ reconcile   — against the partner's own records
```

Two steps in that chain are the whole point:

- **The allocation statement is sealed before the order goes out.** This is what makes
  same-price allocation a property of the design rather than a best effort, and it is
  the control that prevents good fills being cherry-picked between accounts.
- **Each member's rebalance is independent.** One member's delay, limit breach or
  insufficient cash never blocks the other 49. A non-participating member produces a
  *skip with a reason code*, which is a domain outcome, not an error.

## 5. Consistency model

**Strongly consistent (one aggregate, one transaction, optimistic concurrency):**

| Boundary | Guarantee |
| --- | --- |
| Proposal | Ballot uniqueness, window enforcement, decision finality |
| GuildStrategy | One winner per base version; losers rebase |
| MemberRebalance | One active rebalance per account; no duplicate orders |
| OrderBatch | Allocation fixed before submission |

**Eventually consistent (transactional outbox):** fan-out, projections, leagues,
rewards, statements. State change and outgoing event are written in the same
transaction; a publisher drains the outbox; every consumer is idempotent on event id.

**Never a transaction:** Guild-wide completion (a projection), all-or-nothing across
members (legally wrong as well as technically awkward), and trade reversal
(corrections are new, auditable actions).

## 6. Partner integration

Every partner implements the same four operations:

| Operation | Meaning |
| --- | --- |
| `place` | Submit an order or transfer |
| `cancel` | Withdraw an unfilled instruction |
| `positions` | Current holdings, cash, restrictions |
| `reconcile` | Authoritative file for a period |

The adapter owns translation, retries, rate limiting, circuit breaking and error
mapping. **A partner's field names never appear past the adapter.** Domain code sees
domain types only.

Failure handling:

| Failure | Response |
| --- | --- |
| Timeout | Retry under the same idempotency key; then queue the intent |
| 5xx storm | Circuit opens; members see a stated delay, never a failed vote |
| Ambiguous outcome | Never retry blindly — query by our key, reconcile, then decide |
| Rejection | Becomes a skip with a reason code |

## 7. Money and arithmetic

Python will not enforce this, so the codebase does:

- `Money` wraps `Decimal` and **raises on `float` at construction**.
- Weights are integer **basis points**, never floats, so allocations total exactly 100%.
- Division remainders are absorbed deterministically by the firm, never by a member.
- Property tests assert that allocations sum back to the batch total exactly.

See `backend/src/guild/shared/`.

## 8. Agents

Agents draft proposals from a thread, explain a decision's effect before consent, and
monitor for concentration and drift. The harness, not the model, is the design:

- Member intent compiles to **policy**, shown as a diff before it applies.
- **Scopes** are checked in the domain layer, not in a prompt.
- New capabilities run in **shadow mode** against real flows with no authority.
- Golden-case **evals** run in CI; a regression blocks release.
- Retrieval is **member-scoped**; one member's context can never surface in another's.
- Sizing, netting and allocation are **deterministic code**. The agent explains that
  computation; it does not perform it.

## 9. What production adds

The PoC runs on Postgres and Docker Compose. Production (not in this repository)
replaces the outbox poller with change-data-capture into Kafka, splits packages into
services on Kubernetes, and swaps the simulator for real partner adapters. The domain
code is intended to survive that unchanged — which is the entire reason for the
import boundaries.
