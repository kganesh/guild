# ADR 0004 — One brokerage account per member per Guild

**Status:** accepted · **Date:** 2026-10-12

## Context

A member can belong to several Guilds, each with its own strategy. Two Guilds may hold
the same instrument with different target weights. Something has to decide which shares
belong to which group's decision.

## Decision

Each member opens a dedicated individual brokerage account per Guild they join, under
one verified customer record at the clearing firm. Accounts are differentiated by
account number; the Guild name is our label, held in our own mapping.

## Alternative rejected

One account per member, with Guild attribution held as tags in our ledger. Fewer
accounts, lower partner fees, consolidated tax documents — and it makes attribution our
assertion rather than the partner's record, which contradicts ADR 0001.

## Consequences

**Accepted costs:**

- Account count runs ≈1.5× member count; per-account partner fees multiply accordingly.
- Account opening becomes a high-frequency API operation, not a one-time signup step.
- Tax documents and statements are per account, so a member in five Guilds may receive
  five of each. This is an unresolved experience problem.
- Some clearing platforms will not open multiple same-type individual accounts per
  customer at volume. **This is a qualifying question in partner selection**, and the
  decision most likely to be overturned by a partner saying no.

**Bought with those costs:**

- Reconciliation is one-to-one: an account either matches its Guild's target or it does
  not.
- Ownership is never ambiguous when two Guilds hold the same instrument.
- A member falling behind in one Guild has no effect on another.
- The receipt trace works: every share physically sits in the account of the decision
  that created it.

## Fallback

If no partner supports the pattern at volume, revert to ledger-side tagging and accept
reconciliation complexity. Design the ledger so that this swap touches `ledger` and
`recon` only.
