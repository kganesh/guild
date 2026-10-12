# ADR 0002 — Modular monolith first, with enforced boundaries

**Status:** accepted · **Date:** 2026-10-12

## Context

The target production architecture is one service per bounded context. The proof of
concept is built by one person, and its purpose is to demonstrate four invariants and
run a behavioural pilot — not to operate a fleet.

## Decision

One deployable, one package per bounded context (`guild`, `trading`, `ledger`, `recon`,
`adapters`, `agents`), a separate database schema per module, and import boundaries
**enforced in CI** rather than by convention.

Cross-module communication goes through published events or an owned interface. No
module imports another module's internals. No cross-schema queries, even though a
single database makes both trivially easy.

## Alternative rejected

Microservices from day one. Correct for the production team shape, and for a solo build
it is pure overhead: service discovery, deployment pipelines, distributed tracing across
processes, and local development friction — all paid before any of it is needed.

## Consequences

- Extraction later is mechanical: a module with no inbound internal imports and its own
  schema becomes a service by adding transport.
- The boundary rule has to be policed by the linter, because Python makes violating it
  a one-line convenience. **This is the single rule that decides whether the PoC becomes
  version one of production or a rewrite.**
- Local development is `docker compose up` and one process.
- Load characteristics that would justify independent scaling are invisible until the
  split happens, so the production capacity model stays an estimate.
