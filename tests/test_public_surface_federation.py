from __future__ import annotations

from moat.public_surface_federation import (
    GuidedStudioScreen,
    allow_public_claim_from_evidence_pack,
    build_canonical_release_content_bundle,
    build_public_proof_bundle,
    build_public_release_evidence_pack,
    evaluate_docs_surface_health,
    evaluate_public_proof_freshness,
    validate_guided_studio_first_success_flow,
)


def test_dom23_public_proof_bundle_and_freshness() -> None:
    bundle = build_public_proof_bundle(
        release_window="2026-W11",
        benchmark_summary_ref="artifact://benchmark/latest",
        promotion_stage_summary_ref="artifact://promotion/stage",
        external_cohort_summary_ref="artifact://cohort/summary",
        venue_certification_summary_ref="artifact://cert/summary",
        docs_landing_link="https://example.com/docs",
        trust_dashboard_link="https://example.com/trust",
        release_notes_link="https://example.com/release",
    )
    fresh = evaluate_public_proof_freshness(bundle=bundle, max_age_hours=24)
    assert fresh.ready is True


def test_dom24_content_federation_and_health_checks() -> None:
    content = build_canonical_release_content_bundle(
        bundle_id="bundle-1",
        readme_snippets={"intro": "hello"},
        pypi_fragments={"summary": "hello"},
        docs_landing_content={"hero": "hello"},
        in_product_help={"tip": "hello"},
    )
    assert content.bundle_id == "bundle-1"
    health = evaluate_docs_surface_health(
        link_status={"/ok": 200, "/broken": 404},
        command_pairs=[("pqts doctor", "pqts doctor"), ("pqts run", "pqts execute")],
        content_hashes={"readme": "abc", "docs": "def"},
    )
    assert health.healthy is False
    assert "/broken" in health.broken_links


def test_dom26_and_dom27_guided_flow_and_evidence_pack() -> None:
    flow = validate_guided_studio_first_success_flow(
        primary_screens=[
            GuidedStudioScreen("demo", "Demo", "Try demo", "Start demo", "pqts demo", "guided"),
            GuidedStudioScreen("backtest", "Backtest", "Run test", "Run backtest", "pqts run --mode backtest", "guided"),
            GuidedStudioScreen("paper", "Paper", "Start paper", "Start paper", "pqts run --mode paper", "guided"),
        ],
        advanced_surfaces_progressively_disclosed=True,
        max_primary_screens=3,
    )
    assert flow.valid is True

    pack = build_public_release_evidence_pack(
        release_tag="v0.2.0",
        benchmark_status="pass",
        docs_link_health="pass",
        certification_status="pass",
        external_cohort_status="pass",
        trust_limitations=["paper_only_for_new_connector"],
        maturity_state="beta",
    )
    assert allow_public_claim_from_evidence_pack(evidence_pack=pack, claim_kind="readiness") is True
