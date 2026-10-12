"""The Proposal aggregate.

This is where "vote once" is enforced. Every order the platform ever places traces back
to a decision made here, which is why the rules below live in one class with one entry
point rather than being spread across services.

Ballots live inside the boundary because a Guild caps at 50 members — small enough to
load and save as a unit, which is what makes the uniqueness and window rules reliable.
Executions do not: see MemberRebalance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping, Sequence

from guild.shared.weight import Weight, assert_totals_to_one


class ProposalStatus(str, Enum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    #: Approved, but another proposal already moved the strategy on. Rebase and resubmit.
    STALE = "stale"
    APPLIED = "applied"


class BallotChoice(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass(frozen=True, slots=True)
class GovernanceRules:
    """Frozen at submission so a live vote cannot shift under the people voting in it."""

    quorum_bps: int
    approval_threshold_bps: int
    window_hours: int
    close_early_when_decided: bool = True


@dataclass(frozen=True, slots=True)
class Mandate:
    """What a Guild's strategy may contain."""

    allowed_instruments: frozenset[str]
    max_weight_per_instrument: Weight
    excluded_instruments: frozenset[str] = frozenset()


@dataclass(slots=True)
class Ballot:
    member_id: str
    choice: BallotChoice
    cast_at: datetime
    revision: int = 0


@dataclass(frozen=True, slots=True)
class Decision:
    outcome: ProposalStatus
    tally: Mapping[BallotChoice, int]
    decided_at: datetime


class ProposalError(Exception):
    """A domain rule was violated. Never raised for ordinary non-participation."""


@dataclass(slots=True)
class Proposal:
    """Aggregate root. All commands go through this object."""

    id: str
    guild_id: str
    proposer_id: str
    base_version: int
    change: Mapping[str, Weight]
    thesis: str
    conflict_disclosure: str
    electorate: frozenset[str]
    rules: GovernanceRules
    opened_at: datetime
    closes_at: datetime
    status: ProposalStatus = ProposalStatus.OPEN
    decision: Decision | None = None
    ballots: dict[str, Ballot] = field(default_factory=dict)

    # ----- construction -------------------------------------------------------

    @classmethod
    def submit(
        cls,
        *,
        id: str,
        guild_id: str,
        proposer_id: str,
        base_version: int,
        change: Mapping[str, Weight],
        thesis: str,
        conflict_disclosure: str,
        electorate: frozenset[str],
        rules: GovernanceRules,
        mandate: Mandate,
        now: datetime,
    ) -> "Proposal":
        """Invariant 5: the change must satisfy the mandate before anyone can vote."""
        if proposer_id not in electorate:
            raise ProposalError("proposer is not a member of this Guild")
        if not thesis.strip():
            raise ProposalError("a proposal must carry a written thesis")

        assert_totals_to_one(change.values())
        for instrument, weight in change.items():
            if instrument in mandate.excluded_instruments:
                raise ProposalError(f"{instrument} is excluded by the Guild's mandate")
            if instrument not in mandate.allowed_instruments:
                raise ProposalError(f"{instrument} is not an allowed instrument")
            if weight.basis_points > mandate.max_weight_per_instrument.basis_points:
                raise ProposalError(
                    f"{instrument} at {weight} exceeds the mandate cap "
                    f"of {mandate.max_weight_per_instrument}"
                )

        from datetime import timedelta

        return cls(
            id=id,
            guild_id=guild_id,
            proposer_id=proposer_id,
            base_version=base_version,
            change=dict(change),
            thesis=thesis,
            conflict_disclosure=conflict_disclosure,
            electorate=electorate,
            rules=rules,
            opened_at=now,
            closes_at=now + timedelta(hours=rules.window_hours),
        )

    # ----- commands -----------------------------------------------------------

    def cast_ballot(self, member_id: str, choice: BallotChoice, now: datetime) -> None:
        """Invariants 1, 2 and 4."""
        if self.status is not ProposalStatus.OPEN:
            raise ProposalError(f"voting is closed (status={self.status.value})")
        if now >= self.closes_at:
            raise ProposalError("the voting window has expired")
        if member_id not in self.electorate:
            raise ProposalError("not eligible to vote on this proposal")

        existing = self.ballots.get(member_id)
        revision = existing.revision + 1 if existing else 0
        self.ballots[member_id] = Ballot(member_id, choice, now, revision)

        if self.rules.close_early_when_decided and self._outcome_is_certain():
            self._decide(now)

    def withdraw(self, member_id: str, now: datetime) -> None:
        """Invariant 6."""
        if member_id != self.proposer_id:
            raise ProposalError("only the proposer may withdraw a proposal")
        if self.status is not ProposalStatus.OPEN:
            raise ProposalError("only an open proposal can be withdrawn")
        self.status = ProposalStatus.WITHDRAWN
        self.decision = Decision(ProposalStatus.WITHDRAWN, self._tally(), now)

    def close(self, now: datetime) -> None:
        """Called when the window expires."""
        if self.status is not ProposalStatus.OPEN:
            return
        self._decide(now)

    def mark_applied(self, applied_against_version: int) -> None:
        """Invariant 7: applied once, and only against its own base version."""
        if self.status is not ProposalStatus.APPROVED:
            raise ProposalError("only an approved proposal can be applied")
        if applied_against_version != self.base_version:
            self.status = ProposalStatus.STALE
            return
        self.status = ProposalStatus.APPLIED

    # ----- rules --------------------------------------------------------------

    def _tally(self) -> dict[BallotChoice, int]:
        tally = {choice: 0 for choice in BallotChoice}
        for ballot in self.ballots.values():
            tally[ballot.choice] += 1
        return tally

    def _decide(self, now: datetime) -> None:
        tally = self._tally()
        voted = sum(tally.values())
        size = len(self.electorate)

        quorum_met = voted * 10_000 >= self.rules.quorum_bps * size
        approved = tally[BallotChoice.APPROVE] * 10_000 >= (
            self.rules.approval_threshold_bps * size
        )

        outcome = (
            ProposalStatus.APPROVED
            if quorum_met and approved
            else ProposalStatus.REJECTED
            if quorum_met
            else ProposalStatus.EXPIRED
        )
        self.status = outcome
        self.decision = Decision(outcome, tally, now)

    def _outcome_is_certain(self) -> bool:
        """True once no remaining vote can change the result."""
        tally = self._tally()
        size = len(self.electorate)
        outstanding = size - sum(tally.values())
        needed = -(-self.rules.approval_threshold_bps * size // 10_000)
        if tally[BallotChoice.APPROVE] >= needed:
            return True
        return tally[BallotChoice.APPROVE] + outstanding < needed
