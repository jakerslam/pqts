#!/usr/bin/env python3
"""Validate web client alignment with canonical FastAPI v1 contracts."""

from __future__ import annotations

import argparse
from pathlib import Path


ROUTE_PATHS: tuple[str, ...] = (
    "apps/web/app/api/promotion/route.ts",
    "apps/web/app/api/operator/action/route.ts",
    "apps/web/app/api/operator/actions/route.ts",
    "apps/web/app/api/order-truth/route.ts",
    "apps/web/app/api/execution-quality/route.ts",
    "apps/web/app/api/replay/route.ts",
    "apps/web/app/api/template-gallery/route.ts",
    "apps/web/app/api/data-seed/route.ts",
    "apps/web/app/api/notify-test/route.ts",
)


def evaluate_web_api_contracts(*, client_path: Path, route_paths: list[Path]) -> list[str]:
    errors: list[str] = []
    text = client_path.read_text(encoding="utf-8")
    forbidden_tokens = ["/api/v1/account", "/api/v1/positions", "/api/v1/orders", "/api/v1/fills", "/api/v1/risk"]
    for token in forbidden_tokens:
        if token in text:
            errors.append(f"forbidden pseudo-contract path present: {token}")

    required_tokens = [
        "/v1/accounts/",
        "/v1/portfolio/positions",
        "/v1/execution/orders",
        "/v1/execution/fills",
        "/v1/risk/state/",
    ]
    for token in required_tokens:
        if token not in text:
            errors.append(f"missing canonical contract path token: {token}")
    if "Authorization" not in text:
        errors.append("missing Authorization header in web api client")

    forbidden_route_tokens = (
        "@/lib/ops/promotion-store",
        "@/lib/operator/actions",
        "@/lib/ops/reference-data",
        "@/lib/ops/exec",
    )
    required_route_tokens: dict[str, str] = {
        "promotion/route.ts": "/v1/promotions",
        "operator/action/route.ts": "/v1/operator/actions",
        "operator/actions/route.ts": "/v1/operator/actions",
        "order-truth/route.ts": "/v1/ops/order-truth",
        "execution-quality/route.ts": "/v1/ops/execution-quality",
        "replay/route.ts": "/v1/ops/replay",
        "template-gallery/route.ts": "/v1/ops/template-gallery",
        "data-seed/route.ts": "/v1/ops/data-seed",
        "notify-test/route.ts": "/v1/ops/notify/test",
    }
    for route_path in route_paths:
        route_text = route_path.read_text(encoding="utf-8")
        route_label = str(route_path).replace("\\", "/")
        for token in forbidden_route_tokens:
            if token in route_text:
                errors.append(f"forbidden web shim import in {route_label}: {token}")
        if "proxyApi(" not in route_text:
            errors.append(f"missing proxyApi usage in {route_label}")
        expected = next((value for key, value in required_route_tokens.items() if key in route_label), "")
        if expected and expected not in route_text:
            errors.append(f"missing canonical upstream path in {route_label}: {expected}")
    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", default="apps/web/lib/api/client.ts")
    parser.add_argument("--route", action="append", default=list(ROUTE_PATHS))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors = evaluate_web_api_contracts(
        client_path=Path(args.client),
        route_paths=[Path(path) for path in args.route],
    )
    if errors:
        for item in errors:
            print(f"FAIL {item}")
        return 2
    print(f"PASS web api contracts: {args.client}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
