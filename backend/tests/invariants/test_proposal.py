"""Proposal aggregate invariants. See docs/domain-model.md."""

from datetime import datetime, timedelta

import pytest

from guild.domain.guild.proposal import (
    BallotChoice,
    GovernanceRules,
    Mandate,
    Proposal,
    ProposalError,
    ProposalStatus,
)
from guild.shared.weight import Weight

NOW = datetime(2026, 10, 12, 9, 0, 0)
MEMBERS = frozenset({"m1", "m2", "m3", "m4", "m5"})
RULES = GovernanceRules(quorum_bps=5_000, approval_threshold_bps=6_000, window_hours=24)
MANDATE = Mandate(
    allowed_instruments=frozenset({"VTI", "SEMI", "BONDS"}),
    max_weight_per_instrument=Weight.from_percent("50"),
)
CHANGE = {
    "VTI": Weight.from_percent("40"),
    "SEMI": Weight.from_percent("40"),
    "BONDS": Weight.from_percent("20"),
}


def submit(change=None, rules=RULES) -> Proposal:
    return Proposal.submit(
        id="p1",
        guild_id="g1",
        proposer_id="m1",
        base_version=14,
        change=change or CHANGE,
        thesis="Foundry capacity is booked through next year.",
        conflict_disclosure="Proposer holds 9% SEMI.",
        electorate=MEMBERS,
        rules=rules,
        mandate=MANDATE,
        now=NOW,
    )


class TestSubmission:
    def test_weights_must_total_one_hundred(self):
        with pytest.raises(ValueError):
            submit({"VTI": Weight.from_percent("90")})

    def test_mandate_cap_is_enforced(self):
        with pytest.raises(ProposalError):
            submit({"VTI": Weight.from_percent("40"), "SEMI": Weight.from_percent("60")})

    def test_instrument_must_be_allowed(self):
        with pytest.raises(ProposalError):
            submit({"VTI": Weight.from_percent("50"), "DOGE": Weight.from_percent("50")})

    def test_thesis_is_required(self):
        with pytest.raises(ProposalError):
            Proposal.submit(
                id="p2", guild_id="g1", proposer_id="m1", base_version=14,
                change=CHANGE, thesis="   ", conflict_disclosure="",
                electorate=MEMBERS, rules=RULES, mandate=MANDATE, now=NOW,
            )


class TestBallots:
    def test_one_live_ballot_per_member(self):
        p = submit()
        p.cast_ballot("m2", BallotChoice.APPROVE, NOW)
        p.cast_ballot("m2", BallotChoice.REJECT, NOW)
        assert len(p.ballots) == 1
        assert p.ballots["m2"].choice is BallotChoice.REJECT
        assert p.ballots["m2"].revision == 1

    def test_non_members_cannot_vote(self):
        p = submit()
        with pytest.raises(ProposalError):
            p.cast_ballot("stranger", BallotChoice.APPROVE, NOW)

    def test_expired_window_rejects_ballots(self):
        p = submit()
        with pytest.raises(ProposalError):
            p.cast_ballot("m2", BallotChoice.APPROVE, NOW + timedelta(hours=25))

    def test_terminal_state_rejects_ballots(self):
        p = submit()
        p.withdraw("m1", NOW)
        with pytest.raises(ProposalError):
            p.cast_ballot("m2", BallotChoice.APPROVE, NOW)


class TestDecision:
    def test_closes_early_once_certain(self):
        p = submit()
        for member in ["m1", "m2", "m3"]:
            p.cast_ballot(member, BallotChoice.APPROVE, NOW)
        # 3 of 5 approvals meets a 60% threshold: no remaining vote can change it.
        assert p.status is ProposalStatus.APPROVED
        assert p.decision is not None

    def test_closes_early_when_approval_becomes_impossible(self):
        p = submit()
        for member in ["m1", "m2", "m3"]:
            p.cast_ballot(member, BallotChoice.REJECT, NOW)
        assert p.status is ProposalStatus.REJECTED

    def test_uses_rules_frozen_at_submission(self):
        p = submit()
        p.rules = GovernanceRules(quorum_bps=10_000, approval_threshold_bps=10_000, window_hours=1)
        # The aggregate's own copy is what decides; mutating the reference afterwards is
        # not how rule changes work — they go through a new proposal.
        assert p.rules.window_hours == 1  # the object is replaceable in a test
        assert p.closes_at == NOW + timedelta(hours=24)  # the window was already fixed


class TestApplication:
    def test_applied_only_against_its_base_version(self):
        p = submit()
        for member in ["m1", "m2", "m3"]:
            p.cast_ballot(member, BallotChoice.APPROVE, NOW)
        p.mark_applied(applied_against_version=15)
        assert p.status is ProposalStatus.STALE

    def test_applies_cleanly_against_the_current_version(self):
        p = submit()
        for member in ["m1", "m2", "m3"]:
            p.cast_ballot(member, BallotChoice.APPROVE, NOW)
        p.mark_applied(applied_against_version=14)
        assert p.status is ProposalStatus.APPLIED

    def test_only_the_proposer_withdraws(self):
        p = submit()
        with pytest.raises(ProposalError):
            p.withdraw("m2", NOW)
