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
  ↓
CHALLENGED
```

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
* Address: `0x62B2b0eF4b101cd27b93BF138d4c07ce8Ad8Eb54`
* Studio: https://studio.genlayer.com/?import-contract=0x62B2b0eF4b101cd27b93BF138d4c07ce8Ad8Eb54

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

The deployed source corresponds to commit:

```text
8e20da4 Fix corroboration source classification
```

The contract source is located at:

```text
contracts/CorroborationQuorum.py
```
