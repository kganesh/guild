# Agents

Agents draft, explain and monitor. They never compute a number that reaches an order.
See [ADR 0005](../../../../docs/adr/0005-agents-off-the-order-path.md).

## Capabilities

| Capability | What it does | Autonomy at launch |
| --- | --- | --- |
| `draft_proposal` | Turns a chat thread into a structured proposal with a thesis and the counter-arguments listed | Suggest only; a human edits and submits |
| `explain_decision` | States what approving would do to the member's concentration and worst realistic month | Read-only, rendered on the consent card |
| `monitor` | Flags concentration across Guilds, mandate drift, and theses that have gone stale | Read-only, notifies |

## The harness

The harness, not the model, is the design:

- **Policy compilation.** A member's plain-language limits compile to enforceable rules,
  shown as a plan/apply diff before anything takes effect.
- **Scopes** are checked in the domain layer, never in a prompt. An agent's scopes are a
  strict subset of its member's.
- **Member-scoped retrieval.** Every retrieval is filtered to the requesting member's own
  Guilds and holdings. Cross-member retrieval is structurally impossible, not merely
  discouraged.
- **Untrusted input.** A thesis or chat message is member-authored text, fenced as data.
  It can never widen a scope.
- **Shadow mode.** New behaviour runs against real flows with zero authority; outputs are
  compared, never applied.
- **Evals.** Golden cases per capability run in CI on every prompt, model or policy
  change. A regression blocks the release.
- **Tracing.** Every agent action carries a trace id into the same event log as the trades.

## Forbidden

- Price targets, forecasts, or any claim about future returns. The eval suite tests for
  their absence.
- Sizing, netting, lot selection or allocation. That is `domain.trading`, and the import
  linter enforces the separation.
