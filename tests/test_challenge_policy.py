from pathlib import Path


CONTRACT = Path("contracts/CorroborationQuorum.py").read_text(encoding="utf-8")


def test_challenge_is_clerk_only():
    assert 'if rec.clerk != gl.message.sender_address:' in CONTRACT
    assert 'raise Exception("only clerk may challenge")' in CONTRACT


def test_challenge_requires_finalized_state_and_reason():
    assert 'if rec.status not in FINALS:' in CONTRACT
    assert 'raise Exception("nothing to challenge")' in CONTRACT
    assert 'if not clean_reason:' in CONTRACT
    assert 'raise Exception("reason required")' in CONTRACT


def test_challenge_does_not_overwrite_consensus_justification():
    challenge_body = CONTRACT.split(
        "def challenge(self, case_id: str, reason: str) -> None:",
        1,
    )[1].split("@gl.public.view", 1)[0]

    assert 'rec.challenge_reason = clean_reason[:500]' in challenge_body
    assert 'rec.justification =' not in challenge_body


def test_challenge_audit_fields_are_persisted_and_exposed():
    assert 'challenge_reason: str' in CONTRACT
    assert 'challenge_count: u32' in CONTRACT
    assert 'challenge_reason=""' in CONTRACT
    assert 'challenge_count=u32(0)' in CONTRACT
    assert 'rec.challenge_count = u32(int(rec.challenge_count) + 1)' in CONTRACT
    assert '"challenge_reason": rec.challenge_reason' in CONTRACT
    assert '"challenge_count": int(rec.challenge_count)' in CONTRACT
