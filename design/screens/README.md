# Screen mockups

Nineteen static mockups of the member-facing screens, at phone width (390×844).

These are **design artefacts, not application code**. They were authored on a design
canvas and exported here as self-contained HTML so the repository carries its own visual
reference. The `.dc.html` wrapper is the canvas's format; the markup inside each
`<section>` is ordinary HTML and inline CSS, and the screens link to each other, so
opening one in a browser walks the flow.

| Group | Screens |
| --- | --- |
| Getting in | `InviteLanding` · `GuildForming` · `SetRules` · `CreateGuild` · `GuildList` |
| One decision | `Main` (Guild home) · `ProposalBallot` · `CreateProposal` · `ConsentCard` · `RebalanceStatus` |
| Explain and manage | `SkipExplainer` · `AccountOnHold` · `PositionReceipt` · `PortfolioHome` · `AgentBrief` |
| Social and rewards | `MirrorProfile` · `CopyReview` · `Leagues` · `Rewards` |

Start with `Main.dc.html`, then `ProposalBallot` → `ConsentCard` → `RebalanceStatus` →
`PositionReceipt`: that path is the whole product.

**Illustrative content.** Member names, balances, prices and league figures are sample
data. Partner names appear as `[PARTNER FIRM]` and `[BANK]` because none are selected.

When these and the implementation disagree, [`../../docs/ui-spec.md`](../../docs/ui-spec.md)
is the authority on intent, and the mockups are the authority on layout.
