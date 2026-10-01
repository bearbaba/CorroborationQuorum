# CorroborationQuorum

Standalone GenLayer Intelligent Contract.

A claim is not judged from one URL. Each sealed source gets a stance.
Python then applies k-of-n quorum and a contradiction veto.

Flow: `open_case` -> `add_source` -> `seal_sources` -> `adjudicate` -> `challenge`

Status: OPEN -> SEALED -> UPHELD | REFUTED | SPLIT | INCONCLUSIVE -> CHALLENGED

## Consensus

- Nondet only extracts per-URL stance from rendered page text.
- Equivalence is on stance fields, not prose excerpts.
- Final status is computed in code:
  - readable == 0 -> INCONCLUSIVE
  - support >= k and contradict == 0 -> UPHELD
  - support >= 1 and contradict >= 1 -> SPLIT
  - contradict >= k -> REFUTED
  - else -> INCONCLUSIVE

## Deploy

1. Open https://studio.genlayer.com
2. New contract -> paste contracts/CorroborationQuorum.py
3. Deploy
4. Run the 3 cases below. First case id is `1`.

## Studio cases

1. UPHELD
   - predicate: The example.org page refers to IANA.
   - rubric: SUPPORT only if visible text mentions IANA.
   - k: 1
   - sources: https://example.org
   - expect: UPHELD

2. REFUTED
   - predicate: example.org is the official homepage of the United Nations.
   - rubric: CONTRADICT if the page is a generic IANA example and does not present itself as the UN.
   - k: 1
   - sources: https://example.org
   - expect: REFUTED

3. INCONCLUSIVE
   - predicate: This host publishes a live UN charter.
   - rubric: UNREADABLE if the page cannot be fetched.
   - k: 1
   - sources: https://this-domain-should-not-resolve-genlayer-test.invalid
   - expect: INCONCLUSIVE

## Files

- contracts/CorroborationQuorum.py
