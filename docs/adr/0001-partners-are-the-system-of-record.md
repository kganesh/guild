# ADR 0001 — Partners are the system of record

**Status:** accepted · **Date:** 2026-10-12

## Context

Guild does not hold accounts, custody or execution, and will not for 12–24 months.
Clearing firms and sponsor banks do. Our platform orchestrates them.

A middleware platform whose internal ledger drifted from its partner banks' records
produced a bankruptcy where a trustee estimated tens of millions of dollars unaccounted
for. The failure was not a missing feature; it was treating the middleware ledger as
truth and reconciling later.

## Decision

The partner's record is authoritative. Our ledger is an **event-sourced projection**
plus orchestration. Three-way reconciliation — our sub-ledger, the partner's file, and
the event log that produced our state — runs continuously, and a break freezes the
affected account automatically.

## Alternative rejected

Our ledger as the system of record, with partners treated as execution venues and
reconciliation as a batch job. Simpler to build, faster to read, and the exact design
that has already failed in this market.

## Consequences

- Reconciliation is a service with its own SLA, not a nightly script.
- A release gate: reconciliation must run clean in shadow for ten consecutive trading
  days before anything ships.
- Every balance shown to a member carries an implicit claim that we have reconciled it,
  which is why the frozen-account state is a designed screen rather than an error page.
- Rebuilding our state is always possible: restore, then replay against the partner
  files, which are immutable.
