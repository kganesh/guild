"""HTTP surface.

Thin by design: it validates input, resolves the actor, and calls a domain command.
No business rule lives here — rules belong to the aggregate that owns them, so that a
second entry point (a scheduled job, a worker, a future service boundary) cannot bypass
them.
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="Guild",
    version="0.1.0",
    description=(
        "Proof of concept. Partners are simulated, no real money moves, and nothing "
        "here is an offer of any financial product or service."
    ),
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Routers are added milestone by milestone; see docs/implementation-plan.md.
#   M1  /guilds, /proposals, /ballots
#   M2  /rebalances, /consents
#   M3  /batches
#   M5  /ledger, /reconciliation
