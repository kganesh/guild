# ADR 0003 — Batched orders with a sealed pre-trade allocation

**Status:** accepted · **Date:** 2026-10-12

## Context

A Guild decision produces up to 50 member orders in the same instrument. If each is
submitted as it arrives, members receive different prices for the same decision —
which quietly contradicts the product's central promise and creates an obvious
fairness problem between the member who tapped first and the member who tapped last.

Submitting a block and allocating afterwards raises a second problem: whoever
allocates after seeing the fills could direct good prices to favoured accounts.

## Decision

1. Consents collect into a short **batching window**.
2. A **pre-trade allocation statement** — which accounts, how many shares each — is
   written and sealed **before** the order is submitted.
3. One block order goes to the venue.
4. Fills are averaged (volume-weighted) and every account is booked at that single
   price, to four or five decimals.
5. Rounding remainders are absorbed by the firm, deterministically, never by a member.
6. Partial fills allocate pro-rata against the sealed statement, with a minimum viable
   allocation and a documented rotation rule below it.

## Alternative rejected

Per-account sequential orders. Simpler, requires no window, and disperses prices across
members for no reason other than tap order.

## Consequences

- "Everyone in a batch gets the same price" is a property of the design, not an
  aspiration — and it is testable, which is why it is one of the four PoC invariants.
- Members who consent after a window closes land in the next one, and the interface
  must say so rather than implying a single universal price.
- The clearing partner **must** support bunched orders with average-price allocation.
  This is a qualifying question in partner selection, not an integration detail.
- A fill arriving with no sealed statement quarantines the batch.
