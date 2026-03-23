from __future__ import annotations

from app.packaged_launch import evaluate_packaged_launch


def test_packaged_launch_diagnostics() -> None:
    diag = evaluate_packaged_launch(
        flags={
            "python_required": False,
            "unpack_ok": True,
            "risk_router_ok": True,
            "provenance_ok": True,
        }
    )
    assert diag.ok is True
    diag2 = evaluate_packaged_launch(
        flags={
            "python_required": True,
            "unpack_ok": False,
            "risk_router_ok": False,
            "provenance_ok": False,
        }
    )
    assert diag2.ok is False
