# Domain model

The ubiquitous language, the aggregates, and the invariants each one protects. If a
name here and a name in the code disagree, the code is wrong.

## 1. Language

| Term | Meaning |
| --- | --- |
| **Guild** | 2–50 verified members who decide together. Holds no money. |
| **Steward** | Administers membership and settings. One vote, no investment authority. |
| **Guild Strategy** | The group's target allocation, expressed as weights. A desired state, not a fund. |
| **Strategy Version** | An immutable snapshot. Each applied proposal creates one. |
| **Mandate** | What a strategy may hold: allowed assets, caps per instrument, exclusions. |
| **Proposal** | A request to move the strategy from version N to N+1, with a written thesis. |
| **Electorate** | The members eligible to vote, frozen at submission. |
| **Governance Rules** | Quorum, approval threshold, voting window. Frozen per proposal. |
| **Ballot** | One member's vote. Revisable until the window closes. |
| **Guild Account** | A brokerage account in the member's own name, one per Guild. |
| **Strategy View** | Read-only projection across members' accounts. Percentages, never dollars. |
| **Execution Consent** | Confirm Each (default), or Auto-Follow under an advisory agreement. |
| **Rebalance** | Trading one Guild Account toward the current Strategy Version. |
| **Skip Reason** | The coded reason a rebalance did not run. |
| **Conflict Disclosure** | The proposer's existing holdings in the affected instruments. |

**Words this codebase never uses** — in identifiers, schemas, or copy: *pool, vault,
fund, manager, leader* (inside a Guild), *shares, equity, dividend, yield* (for
bonuses), *guaranteed*. Names leak from schema into interface, and the interface is
what a regulator reads.

## 2. Aggregates

### Proposal (the primary aggregate)

```
Proposal «root»                      id: ProposalId
├── guildId, proposerId              references by ID only
├── baseVersion                      «VO» StrategyVersionRef
├── change                            «VO» TargetAllocation → AllocationLine[]
├── thesis, conflictDisclosure        «VO»
├── electorate                        «VO» member ids, frozen at submit
├── rules                             «VO» quorum, threshold, window
├── status                            «VO» state machine
├── decision                          «VO» outcome, tally, decidedAt
└── ballots: Ballot[]                 «entity» identity = (ProposalId, MemberId)
```

**Invariants the root enforces:**

1. Only electorate members vote; at most one live ballot each.
2. Ballots accepted only while `Open` and the window is unexpired.
3. Decisions use the rules frozen at submission; voting closes early once the outcome
   cannot change.
4. Terminal states accept no further ballots.
5. The change satisfies the Mandate: weights total exactly 100%, caps hold, instruments
   allowed.
6. Only the proposer withdraws, and only while `Open`.
7. A proposal is applied once, and only against its own base version.

**Why ballots are inside and executions are not.** A Guild caps at 50 members, so a
Proposal carries at most 50 ballots — small enough to load and save as a unit, which is
what lets the root enforce rules 1–4 reliably. Fifty concurrent fills would contend on
one lock and have a lifecycle that outlives the vote, so `MemberRebalance` is its own
aggregate referenced by id.

### Other aggregates

| Aggregate | Contains | Key invariant |
| --- | --- | --- |
| `Guild` | Membership; governance rules; mandate | ≤50 members, ≥1 Steward, supermajority to change rules |
| `GuildStrategy` | Strategy version history | Versions increase monotonically; applies only against the current version |
| `MemberRebalance` | Order intent refs, skip reason, consent record | Exactly one per (member, version); terminal once completed or skipped |
| `OrderBatch` | Order intents, allocation statement, fills | Allocation sealed before submission; every account gets the same average price |
| `Pact` | Participants, schedule, bonus rules | Bonus counts only confirmed contributions |

## 3. Domain events

`ProposalSubmitted` · `BallotCast` · `ProposalApproved` · `ProposalWentStale` ·
`StrategyVersionPublished` · `MemberRebalanceRequested` · `MemberRebalanceSkipped` ·
`OrderBatchSubmitted` · `OrderFilled` · `MemberRebalanceCompleted` ·
`ReconciliationBreakDetected` · `AccountFrozen`

Every one is written to the outbox in the same transaction as the state change that
produced it.

## 4. Skip reasons

A skip is a normal outcome, not a failure. The codes are part of the domain and surface
directly to the member:

| Code | Member-facing meaning |
| --- | --- |
| `CONSENT_MISSING` | Did not approve in time |
| `CONSENT_TIMED_OUT` | The consent window closed |
| `INSUFFICIENT_CASH` | Not enough available in the account |
| `BELOW_MINIMUM_TRADE` | Share too small to place; rolls into the next rebalance |
| `ACCOUNT_RESTRICTED` | The account cannot trade right now |
| `LIMIT_EXCEEDED` | The member's own per-decision limit would be breached |
| `STATE_NOT_COVERED` | Not available in this member's state |

## 5. Race conditions closed by design

| Race | Closure |
| --- | --- |
| Two proposals approved against one base version | Compare-and-set; the loser rebases |
| Proposer sells ahead of their own Guild | Restriction starts at submission, not approval |
| Stale eligibility at order time | Layered checks; the partner's rejection is authoritative and becomes a skip |
| Duplicate consent taps | Idempotency key per (member, version) |
| Fill arrives before allocation persists | Allocation sealed pre-trade; an unmatched fill quarantines the batch |
