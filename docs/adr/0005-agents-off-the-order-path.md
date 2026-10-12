# ADR 0005 — Agents are never on the critical order path

**Status:** accepted · **Date:** 2026-10-12

## Context

Agents are a real part of the product: they draft a proposal from a chat thread, adapt
a group decision to a member's account, explain what it does to their risk before they
consent, and watch for concentration building across Guilds.

The tempting next step is to let the model compute the numbers it is explaining.

## Decision

Sizing, netting, lot selection, allocation and limit enforcement are **deterministic
code**. The agent explains that computation; it never performs it. No model output ever
becomes a quantity, a price, or an order.

Agent capabilities are governed by a harness:

- Member intent compiles to policy, shown as a plan/apply diff before it takes effect.
- Scopes are enforced in the domain layer, not in a prompt.
- New behaviour runs in shadow mode against real flows with zero authority.
- Golden-case evals run in CI; a regression blocks release.
- Retrieval is member-scoped; cross-member retrieval is structurally impossible.
- Member-authored text (a thesis, a chat message) is fenced as untrusted data and can
  never widen a scope.

## Alternative rejected

Agent-computed sizing, with guardrails and review. It would be faster to build and
immediately more impressive in a demo. It also makes every arithmetic error a
probabilistic one, and makes "why did my account buy this?" unanswerable with
certainty.

## Consequences

- Agent latency never blocks an order; the order path has no model call in it.
- The agent layer can be rewritten, re-prompted or swapped between providers without
  any risk to execution correctness.
- Capability growth is a ladder — suggest, approve-each, bounded automation — and each
  rung has to be earned with evidence rather than configured at signup.
- Some genuinely useful automation ships later than it could have.
