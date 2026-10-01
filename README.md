# CorroborationQuorum

Standalone GenLayer Intelligent Contract.

A claim is not judged from one URL. Each sealed source gets a stance.
Python applies k-of-n quorum and a contradiction veto.

Flow: `open_case` -> `add_source` -> `seal_sources` -> `adjudicate` -> `challenge`

Status: OPEN -> SEALED -> UPHELD | REFUTED | SPLIT | INCONCLUSIVE -> CHALLENGED

## Consensus

- Validators independently render each sealed URL with `web.render(mode="html")`.
- Stance is derived from page bytes plus the predicate.
- Equivalence is `strict_eq` on canonical JSON `{url, stance}`.
- Final status is computed in code:
  - readable == 0 -> INCONCLUSIVE
  - support >= k and contradict == 0 -> UPHELD
  - support >= 1 and contradict >= 1 -> SPLIT
  - contradict >= k -> REFUTED
  - else -> INCONCLUSIVE

## Deployed

- Network: Studionet (61999)
- Address: 0x5978d51221A08F0515E84BD1CC9BBa4805042dce
- Studio: https://studio.genlayer.com/?import-contract=0x5978d51221A08F0515E84BD1CC9BBa4805042dce
- Explorer: https://explorer-studio.genlayer.com/address/0x5978d51221A08F0515E84BD1CC9BBa4805042dce
- Source: contracts/CorroborationQuorum.py

## Studio cases

1. UPHELD
   - The example.org page refers to IANA.
   - SUPPORT if page text contains IANA.
   - https://example.org
   - result: SUPPORT -> UPHELD

2. REFUTED
   - example.org is the official homepage of the United Nations.
   - CONTRADICT if page does not contain United Nations.
   - https://example.org
   - result: CONTRADICT -> REFUTED

3. INCONCLUSIVE
   - This host publishes a live UN charter.
   - UNREADABLE if fetch fails.
   - https://this-domain-should-not-resolve-genlayer-test.invalid
   - result: UNREADABLE -> INCONCLUSIVE
