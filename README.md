# CorroborationQuorum

A standalone GenLayer Intelligent Contract for multi-source claim corroboration.

Each sealed source is evaluated independently against the supplied predicate and rubric. Every source receives exactly one normalized stance:

* `SUPPORT`
* `CONTRADICT`
* `IRRELEVANT`
* `UNREADABLE`

The contract then applies deterministic `k-of-n` quorum logic with a contradiction veto. The final status is computed from the per-source stances and is not a free-form model verdict.

## Workflow

```text
open_case
    ↓
add_source
    ↓
seal_sources
    ↓
adjudicate
    ↓
get_case
    ↓
challenge
```

State flow:

```text
OPEN
  ↓
SEALED
  ↓
UPHELD | REFUTED | SPLIT | INCONCLUSIVE
  ↓  clerk-only challenge
CHALLENGED
  ↓  adjudicate again
UPHELD | REFUTED | SPLIT | INCONCLUSIVE
```

## Challenge authorization

A finalized result cannot be challenged by an arbitrary caller.

Only the address stored as the case `clerk` when `open_case` was called may invoke `challenge`.

The challenge transition now enforces:

```text
sender == case.clerk
status in UPHELD | REFUTED | SPLIT | INCONCLUSIVE
reason is non-empty
```

A challenge writes to a dedicated `challenge_reason` field and increments
`challenge_count`. It does **not** overwrite `justification`, which remains
the deterministic explanation of the most recently finalized consensus round.

This prevents unrelated addresses from repeatedly invalidating settled cases
or replacing their consensus justification.

## Source evaluation

During `adjudicate`, every sealed URL is rendered and evaluated against the exact predicate and rubric supplied for the case.

The classifier does not contain hard-coded IANA or United Nations branches. The same evaluation procedure is applied to every sealed source.

Readable sources are classified as:

* `SUPPORT` — the source provides sufficient evidence supporting the predicate under the rubric.
* `CONTRADICT` — the source provides sufficient evidence contradicting the predicate under the rubric.
* `IRRELEVANT` — the source is readable but does not provide sufficient relevant evidence either way.
* `UNREADABLE` — the source cannot be successfully rendered or evaluated.

The nondeterministic source evaluation is executed with an independent validator. The validator checks that the returned URL ordering and normalized stance for every sealed source match its own evaluation before the result is accepted.

## Final status logic

For `k` accepted supporting or contradicting sources:

1. If every source is unreadable → `INCONCLUSIVE`
2. If `CONTRADICT >= k` → `REFUTED`
3. If `SUPPORT >= k` and there are no contradictions → `UPHELD`
4. If there is at least one support and at least one contradiction → `SPLIT`
5. Otherwise → `INCONCLUSIVE`

This preserves the contradiction veto while keeping the final aggregation deterministic.

## Live deployment

* Network: Studionet
* Corrected address: `0x72C8b0062D38f990Eb5Bd0c2E890C730976B7Eff`
* Studio: https://studio.genlayer.com/?import-contract=0x72C8b0062D38f990Eb5Bd0c2E890C730976B7Eff
* Explorer: https://explorer-studio.genlayer.com/address/0x72C8b0062D38f990Eb5Bd0c2E890C730976B7Eff

The previous deployment `0x62B2b0eF4b101cd27b93BF138d4c07ce8Ad8Eb54`
is superseded and should not be used for review.

### Live challenge authorization verification

A finalized case was created by clerk:

`0x4C7cb73aC8F8999af21cfc9fF4cF2333a9508Dcb`

with result:

```text
status            = UPHELD
justification     = k=1 support=1 contradict=0 readable=1
challenge_reason  = ""
challenge_count   = 0
round_no          = 1
```

An unrelated address:

`0xD6b8A3A5eB329410D9504784812b8569afA8C2aF`

attempted to challenge the finalized case. The case state remained unchanged,
demonstrating that an unauthorized caller cannot move the case to
`CHALLENGED` or overwrite the finalized justification.

The clerk then challenged the same case successfully. The resulting state was:

```text
status            = CHALLENGED
justification     = k=1 support=1 contradict=0 readable=1
challenge_reason  = clerk requested reconsideration
challenge_count   = 1
round_no          = 1
```

This verifies both required security properties: challenge authority is limited
to the case clerk, and the previous consensus justification is preserved instead
of being overwritten by the challenge reason.

## Verified cases

### Case 1 — SUPPORT across multiple sources

Predicate:

> The IANA-managed example domain is reserved for documentation examples.

With `k=2`:

| Source                                 | Stance       |
| -------------------------------------- | ------------ |
| `https://www.iana.org/domains/example` | `SUPPORT`    |
| `https://www.un.org/`                  | `UNREADABLE` |
| `https://example.com/`                 | `SUPPORT`    |

Result:

```text
support_n    = 2
contradict_n = 0
readable_n   = 2
status       = UPHELD
```

This demonstrates that a non-IANA source can independently produce `SUPPORT`.

### Case 3 — independent evaluation of all sealed sources

Predicate:

> The United Nations is headquartered in New York City.

With `k=1`:

| Source                                 | Stance       |
| -------------------------------------- | ------------ |
| `https://www.un.org/en/about-us`       | `UNREADABLE` |
| `https://www.iana.org/domains/example` | `IRRELEVANT` |
| `https://example.com/`                 | `IRRELEVANT` |

Result:

```text
support_n    = 0
contradict_n = 0
readable_n   = 2
status       = INCONCLUSIVE
```

This demonstrates that every sealed source is processed and that readable-but-non-evidentiary sources are distinguished from unreadable sources.

### Case 4 — CONTRADICT and contradiction veto

Predicate:

> The IANA-managed example domain is NOT reserved for documentation examples.

With `k=1`:

| Source                                 | Stance       |
| -------------------------------------- | ------------ |
| `https://www.iana.org/domains/example` | `CONTRADICT` |
| `https://example.com/`                 | `CONTRADICT` |

Result:

```text
support_n    = 0
contradict_n = 2
readable_n   = 2
status       = REFUTED
```

This demonstrates that the classifier can produce `CONTRADICT` for multiple independently evaluated sources and that the contradiction veto produces `REFUTED`.

## Source version

The corrected challenge authorization logic was introduced by:

```text
dbff5a0 Protect challenge transition from arbitrary callers
```

Regression coverage was added in:

```text
db5ec4e Add regression tests for challenge authorization
```

The deployed contract source matches:

```text
contracts/CorroborationQuorum.py
```

on the current `main` branch. Subsequent README updates do not modify the
deployed contract source.
