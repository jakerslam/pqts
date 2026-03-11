from __future__ import annotations

from pathlib import Path

from tools.check_web_api_contracts import evaluate_web_api_contracts


def test_web_api_contracts_pass_for_canonical_paths(tmp_path: Path) -> None:
    client = tmp_path / "client.ts"
    client.write_text(
        """
        fetch("http://localhost:8000/v1/accounts/paper-main", { headers: { Authorization: "Bearer x" } });
        fetch("http://localhost:8000/v1/portfolio/positions?account_id=paper-main");
        fetch("http://localhost:8000/v1/execution/orders?account_id=paper-main");
        fetch("http://localhost:8000/v1/execution/fills?account_id=paper-main");
        fetch("http://localhost:8000/v1/risk/state/paper-main");
        """,
        encoding="utf-8",
    )
    route = tmp_path / "route.ts"
    route.write_text(
        """
        import { proxyApi } from "@/lib/api/server-proxy";
        export async function GET() { return proxyApi("/v1/ops/replay"); }
        """,
        encoding="utf-8",
    )
    assert evaluate_web_api_contracts(client_path=client, route_paths=[route]) == []


def test_web_api_contracts_flag_legacy_paths(tmp_path: Path) -> None:
    client = tmp_path / "client.ts"
    client.write_text(
        """
        fetch("/api/v1/account");
        fetch("/api/v1/orders");
        """,
        encoding="utf-8",
    )
    route = tmp_path / "route.ts"
    route.write_text(
        """
        import { listOperatorActions } from "@/lib/operator/actions";
        export async function GET() { return listOperatorActions(); }
        """,
        encoding="utf-8",
    )
    errors = evaluate_web_api_contracts(client_path=client, route_paths=[route])
    assert any("forbidden pseudo-contract path" in item for item in errors)
    assert any("missing canonical contract path token" in item for item in errors)
    assert any("forbidden web shim import" in item for item in errors)
    assert any("missing proxyApi usage" in item for item in errors)
