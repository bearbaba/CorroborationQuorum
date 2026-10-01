# CorroborationQuorum

A standalone GenLayer primitive for multi-source claims.

Each sealed URL receives one stance. Python then applies k-of-n quorum
and a contradiction veto. The final status is not a free-form model verdict.

`open_case` → `add_source` → `seal_sources` → `adjudicate` → `challenge`

OPEN → SEALED → UPHELD | REFUTED | SPLIT | INCONCLUSIVE → CHALLENGED

## How consensus is used

Validators render the same sealed pages with `web.render(mode="html")`.
They agree with `strict_eq` on canonical `{url, stance}` JSON.
Status is computed from those stances in contract code.

## Live deployment

- Network: Studionet
- Address: `0x5978d51221A08F0515E84BD1CC9BBa4805042dce`
- Studio: https://studio.genlayer.com/?import-contract=0x5978d51221A08F0515E84BD1CC9BBa4805042dce
- Explorer: https://explorer-studio.genlayer.com/address/0x5978d51221A08F0515E84BD1CC9BBa4805042dce

## Verified cases

| Id | Result | Why |
| --- | --- | --- |
| 1 | UPHELD | example.org HTML contains IANA |
| 2 | REFUTED | example.org is not the UN homepage |
| 3 | INCONCLUSIVE | invalid host is UNREADABLE |
