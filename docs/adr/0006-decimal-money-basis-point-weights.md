# ADR 0006 — Decimal money, basis-point weights, floats rejected

**Status:** accepted · **Date:** 2026-10-12

## Context

The PoC is written in Python, which will not stop money arithmetic being done in
floating point:

```python
price = 62.594
shares = 8.2114
total = price * shares     # 513.99998... and no complaint
```

Three places in Guild where that matters:

- **Allocation.** A block filling at six prices, averaged, split across 38 accounts.
  Float drift gives two members prices that differ in the fourth decimal — breaking the
  invariant ADR 0003 exists to guarantee.
- **Weights.** Targets that must total exactly 100%. In floats,
  `0.4 + 0.28 + 0.19 + 0.13` is not reliably `1.0`.
- **Division.** Splitting a batch leaves a remainder. Someone must absorb the fraction
  of a cent, deterministically.

## Decision

- `Money` wraps `Decimal` and **raises `TypeError` on a `float`** at construction.
- Weights are integer **basis points** (0–10,000), never percentages as floats.
- Remainders from allocation are absorbed by the firm, by an explicit rule, never
  distributed to whichever member rounds last.
- A lint rule bans `float` in domain packages.
- Property tests assert that allocations sum back to the batch total exactly, and that
  weights total exactly 10,000 basis points.

## Alternative rejected

Floats with rounding applied at the display edge. Universally tempting, universally
fine until the day it is not, and undetectable in tests that only check to two decimals.

## Consequences

- Three mechanisms (a type, a lint rule, property tests) do the job a static type
  system would do for free. They must be maintained deliberately.
- Construction from a float is a hard error, so callers must pass `Decimal` or `str` —
  slightly more ceremony at every boundary.
- If the money path later moves to Kotlin, these guarantees become compiler-enforced
  and the discipline can relax.
