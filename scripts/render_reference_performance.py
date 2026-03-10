#!/usr/bin/env python3
"""Render reference performance artifacts into docs and README."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
START_MARKER = "<!-- REFERENCE_PERFORMANCE:START -->"
END_MARKER = "<!-- REFERENCE_PERFORMANCE:END -->"


@dataclass(frozen=True)
class BundleSummary:
    bundle: str
    path: str
    leaderboard_path: str
    report_path: str
    markets: str
    strategies: str
    avg_quality_score: float
    avg_fill_rate: float
    avg_reject_rate: float
    total_submitted: float
    total_filled: float
    total_rejected: float

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "BundleSummary":
        summary = payload.get("summary", {}) or {}
        return cls(
            bundle=str(payload.get("bundle", "")),
            path=str(payload.get("path", "")),
            leaderboard_path=str(payload.get("leaderboard_path", "")),
            report_path=str(payload.get("report_path", "")),
            markets=str(payload.get("markets", "")),
            strategies=str(payload.get("strategies", "")),
            avg_quality_score=float(summary.get("avg_quality_score", 0.0) or 0.0),
            avg_fill_rate=float(summary.get("avg_fill_rate", 0.0) or 0.0),
            avg_reject_rate=float(summary.get("avg_reject_rate", 0.0) or 0.0),
            total_submitted=float(summary.get("total_submitted", 0.0) or 0.0),
            total_filled=float(summary.get("total_filled", 0.0) or 0.0),
            total_rejected=float(summary.get("total_rejected", 0.0) or 0.0),
        )

    @property
    def bundle_readme(self) -> str:
        return f"{self.path}/README.md"

    @property
    def leaderboard_rel(self) -> str:
        return self.leaderboard_path

    @property
    def report_rel(self) -> str:
        return self.report_path


def _load_summaries(path: Path) -> tuple[datetime, list[BundleSummary]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_generated_at = str(payload.get("generated_at", ""))
    generated_at = datetime.fromisoformat(raw_generated_at.replace("Z", "+00:00"))
    rows = [BundleSummary.from_payload(row) for row in payload.get("bundles", [])]
    if not rows:
        raise ValueError(f"No bundles found in {path}")
    return generated_at, rows


def _best_bundle(rows: list[BundleSummary]) -> BundleSummary:
    return max(rows, key=lambda row: (row.avg_quality_score, row.avg_fill_rate, -row.avg_reject_rate))


def _render_readme_block(generated_at: datetime, rows: list[BundleSummary]) -> str:
    best = _best_bundle(rows)
    lines = [
        START_MARKER,
        f"_Last generated (UTC): {generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        f"- `{best.bundle}` ([bundle]({best.bundle_readme}), [csv]({best.leaderboard_rel}), [report]({best.report_rel}))",
        f"  - `avg_quality_score={best.avg_quality_score:.4f}`",
        f"  - `avg_fill_rate={best.avg_fill_rate:.4f}`",
        f"  - `avg_reject_rate={best.avg_reject_rate:.4f}`",
        f"  - `total_filled={best.total_filled:.0f}` / `total_submitted={best.total_submitted:.0f}`",
        "",
        "| Bundle | Markets | Strategy | Quality | Fill | Reject |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda item: item.bundle):
        lines.append(
            "| `{bundle}` | `{markets}` | `{strategy}` | `{quality:.4f}` | `{fill:.4f}` | `{reject:.4f}` |".format(
                bundle=row.bundle,
                markets=row.markets,
                strategy=row.strategies,
                quality=row.avg_quality_score,
                fill=row.avg_fill_rate,
                reject=row.avg_reject_rate,
            )
        )
    lines.append(END_MARKER)
    lines.append("")
    return "\n".join(lines)


def _update_readme(readme_path: Path, block: str) -> None:
    content = readme_path.read_text(encoding="utf-8")
    start = content.find(START_MARKER)
    end = content.find(END_MARKER)
    if start < 0 or end < 0 or end < start:
        raise ValueError(
            f"Could not find marker block in {readme_path}. "
            f"Expected {START_MARKER} ... {END_MARKER}"
        )
    end += len(END_MARKER)
    updated = content[:start] + block.rstrip() + content[end:]
    readme_path.write_text(updated, encoding="utf-8")


def _render_doc(generated_at: datetime, rows: list[BundleSummary]) -> str:
    best = _best_bundle(rows)
    bundle_link = f"../{best.bundle_readme}"
    csv_link = f"../{best.leaderboard_rel}"
    report_link = f"../{best.report_rel}"
    lines = [
        "# Reference Performance",
        "",
        f"Last generated (UTC): {generated_at.astimezone(timezone.utc).isoformat()}",
        "",
        "This file is generated from `results/reference_performance_latest.json`.",
        "",
        "## Highlight",
        "",
        f"- Best bundle by quality: `{best.bundle}`",
        f"- Metrics: quality `{best.avg_quality_score:.4f}`, fill `{best.avg_fill_rate:.4f}`, reject `{best.avg_reject_rate:.4f}`",
        f"- Artifacts: [bundle]({bundle_link}), [csv]({csv_link}), [report]({report_link})",
        "",
        "## Bundle Table",
        "",
        "| Bundle | Markets | Strategy | Submitted | Filled | Rejected | Quality | Fill | Reject |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda item: item.bundle):
        lines.append(
            "| `{bundle}` | `{markets}` | `{strategy}` | {submitted:.0f} | {filled:.0f} | {rejected:.0f} | {quality:.4f} | {fill:.4f} | {reject:.4f} |".format(
                bundle=row.bundle,
                markets=row.markets,
                strategy=row.strategies,
                submitted=row.total_submitted,
                filled=row.total_filled,
                rejected=row.total_rejected,
                quality=row.avg_quality_score,
                fill=row.avg_fill_rate,
                reject=row.avg_reject_rate,
            )
        )
    lines.extend(
        [
            "",
            "## Regeneration",
            "",
            "```bash",
            "python3 scripts/publish_reference_bundles.py --config config/paper.yaml --out-root results",
            "python3 scripts/render_reference_performance.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="results/reference_performance_latest.json",
        help="Input JSON from publish_reference_bundles.py",
    )
    parser.add_argument(
        "--readme",
        default="README.md",
        help="README path containing REFERENCE_PERFORMANCE markers",
    )
    parser.add_argument(
        "--doc-out",
        default="docs/REFERENCE_PERFORMANCE.md",
        help="Output markdown file path",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    generated_at, rows = _load_summaries(ROOT / args.input)
    readme_block = _render_readme_block(generated_at, rows)
    _update_readme(ROOT / args.readme, readme_block)
    doc_text = _render_doc(generated_at, rows)
    (ROOT / args.doc_out).write_text(doc_text, encoding="utf-8")
    print(
        json.dumps(
            {
                "input": str(args.input),
                "readme": str(args.readme),
                "doc_out": str(args.doc_out),
                "bundle_count": len(rows),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
