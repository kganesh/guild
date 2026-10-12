# UI specification

The full screen-by-screen specification lives alongside this repository; this is the
contributor-facing summary: the principles every screen obeys, the inventory, and the
rules that are not style choices.

Static mockups of the key screens are in [`../design/screens/`](../design/screens/).

## Principles

1. **Percentages are social, dollars are private.** Anything another member can see is a
   weight, a rank or a participation count. A member's balance is never visible to
   anyone else, on any screen.
2. **Consent is an act, never a default.** Every order was either tapped by the member or
   pre-authorised by them in a setting they wrote.
3. **Every balance carries its label.** Cash, invested and borrowed are visually distinct
   and named wherever a total appears.
4. **The group's state and the member's state are always separable.**
5. **Every position is explainable.** One tap from any holding reaches the decision, the
   vote and the thesis that produced it.
6. **Skips are normal, not failures.** Non-participation is stated plainly with a reason
   and a next action.

## Screen inventory

**Enrollment:** invite landing · identity capture · verification pending · account
opening · funding · set your rules · catch-up to strategy · Guild forming · state
waitlist

**Guild:** Guild list · Guild home (Strategy View) · proposal detail and ballot · create
proposal · create a Guild · Guild settings and governance · members · Pact

**Execution:** consent card · rebalance status · skip explainer · account on hold ·
position detail and receipt

**Member:** portfolio home · money in and out · card and spending · send to a member ·
activity and notifications · agent brief · Mirror profile · following and connections ·
copy review · leagues and season · rewards · settings (limits and autonomy) ·
authorisations and consent history · documents and statements · help and support

## Rules that are not style choices

- **The consent card** must be readable in ten seconds. Skip carries the same visual
  weight as Approve. Expiry is stated as a time, never a countdown ring — countdown
  pressure on a financial consent is manipulative.
- **The tally is hidden** until a member has voted. Visible running tallies produce
  herding.
- **Conflict disclosure** sits adjacent to the thesis, not below it, and states the
  proposer's holding as a percentage of their own account.
- **No projections.** No forecast returns, no growth curves into the future.
- **Performance always carries context:** its period, and either a benchmark or a risk
  measure beside it.
- **Colour never carries meaning alone.** Gains, losses, approve and reject each pair
  colour with a label, an icon or a sign.
- **Estimates are labelled** as estimates until filled.

## Banned vocabulary

In copy, identifiers and schemas alike: *pool, vault, fund, manager, leader* (inside a
Guild), *shares, equity, dividend, yield* (for bonuses), *guaranteed, risk-free*. Names
leak from schema into interface, and the interface is what a regulator reads.
