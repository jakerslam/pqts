from __future__ import annotations

from adapters.prediction_market_streaming import (
    BuilderScope,
    LocalSigner,
    RemoteSigner,
    SignRequest,
    StreamHealthTracker,
)


def test_stream_health_tracker_disconnect_cancel_policy() -> None:
    tracker = StreamHealthTracker(disconnect_cancel_enabled=True)
    tracker.on_connected()
    report = tracker.on_disconnect(reason="socket_timeout")
    assert report["cancel_triggered"] is True
    assert tracker.protected_cancel_events == 1
    tracker.on_gap_recovery(sequence_from=10, sequence_to=20)
    status = tracker.status()
    assert status["reconnect_attempts"] == 1
    assert status["gap_recovery_events"] == 1


def test_local_and_remote_signers_return_deterministic_contract_strings() -> None:
    req = SignRequest(payload="abc", key_id="k1")
    local = LocalSigner().sign(req)
    remote = RemoteSigner("https://signer.example").sign(req)
    assert local.startswith("local_sig::k1::")
    assert remote.startswith("remote_sig::https://signer.example::k1::")


def test_builder_scope_contract_fields() -> None:
    scope = BuilderScope(
        name="institutional_builder",
        can_trade=True,
        can_withdraw=False,
        can_manage_api_keys=True,
    )
    assert scope.can_trade is True
    assert scope.can_withdraw is False
