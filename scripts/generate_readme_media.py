#!/usr/bin/env python3
"""Generate deterministic README visual assets (PNG + GIF) in docs/media."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "docs" / "media"
RESULTS_DIR = ROOT / "results"


BG = (12, 18, 34)
CARD = (24, 34, 58)
ACCENT = (84, 214, 174)
TEXT = (230, 236, 246)
MUTED = (152, 168, 196)
RED = (239, 68, 68)
BLUE = (96, 165, 250)
GREEN = (34, 197, 94)


def _canvas(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (1280, 720), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((40, 30, 1240, 690), outline=(44, 62, 96), width=2)
    draw.text((70, 60), title, fill=TEXT)
    if subtitle:
        draw.text((70, 90), subtitle, fill=MUTED)
    return img, draw


def _bundles() -> list[Path]:
    rows = sorted(path for path in RESULTS_DIR.glob("2026-03-09_*") if path.is_dir())
    return rows


def _first_csv_row(csv_path: Path) -> dict[str, str]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle), None)
    return dict(row or {})


def _latest_bundle_metric_rows() -> list[dict[str, str]]:
    bundles = _bundles()
    if not bundles:
        return []
    latest = bundles[-1]
    csv_files = sorted(latest.glob("simulation_leaderboard_*.csv"))
    if not csv_files:
        return []
    with csv_files[-1].open("r", encoding="utf-8", newline="") as handle:
        return [dict(item) for item in csv.DictReader(handle)]


def _save(img: Image.Image, name: str) -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    img.save(MEDIA_DIR / name)


def _draw_metric_box(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, value: str, color: tuple[int, int, int]) -> None:
    draw.rounded_rectangle((x, y, x + 340, y + 120), radius=14, fill=CARD, outline=(48, 70, 110), width=2)
    draw.text((x + 18, y + 20), label, fill=MUTED)
    draw.text((x + 18, y + 56), value, fill=color)


def make_dashboard_overview() -> None:
    img, draw = _canvas("PQTS Dashboard Overview", "Operational posture and live controls")
    _draw_metric_box(draw, 80, 160, "Mode", "Paper Trading", BLUE)
    _draw_metric_box(draw, 450, 160, "Risk State", "Healthy", GREEN)
    _draw_metric_box(draw, 820, 160, "Active Markets", "crypto / equities / forex", ACCENT)
    _draw_metric_box(draw, 80, 320, "Canary Decision", "hold", BLUE)
    _draw_metric_box(draw, 450, 320, "Critical Alerts", "0", GREEN)
    _draw_metric_box(draw, 820, 320, "Promotion Gate", "unknown", MUTED)
    _draw_metric_box(draw, 80, 480, "Automation", "enabled", ACCENT)
    _draw_metric_box(draw, 450, 480, "CI Status", "passing", GREEN)
    _draw_metric_box(draw, 820, 480, "Coverage", "workflow enabled", BLUE)
    _save(img, "dashboard_overview.png")


def make_simulation_leaderboard() -> None:
    rows = _latest_bundle_metric_rows()
    img, draw = _canvas("Simulation Leaderboard", "Top strategy rows from reproducible bundle")
    draw.rounded_rectangle((70, 140, 1210, 650), radius=16, fill=CARD, outline=(48, 70, 110), width=2)
    headers = ["market", "strategy", "runs", "quality", "fill", "reject"]
    x_cols = [100, 260, 520, 650, 820, 980]
    for x, header in zip(x_cols, headers):
        draw.text((x, 170), header.upper(), fill=MUTED)
    y = 220
    for row in rows[:8]:
        draw.text((x_cols[0], y), str(row.get("market", "")), fill=TEXT)
        draw.text((x_cols[1], y), str(row.get("strategy", "")), fill=TEXT)
        draw.text((x_cols[2], y), str(row.get("runs", "")), fill=TEXT)
        draw.text((x_cols[3], y), f"{float(row.get('avg_quality_score', 0.0)):.2f}", fill=ACCENT)
        draw.text((x_cols[4], y), f"{float(row.get('avg_fill_rate', 0.0)):.2f}", fill=BLUE)
        draw.text((x_cols[5], y), f"{float(row.get('avg_reject_rate', 0.0)):.2f}", fill=RED)
        y += 52
    _save(img, "simulation_leaderboard.png")


def make_risk_controls() -> None:
    img, draw = _canvas("Risk Control Surface", "Kill-switch, limits, and guardrails")
    cards = [
        ("Kill Switch", "armed", GREEN),
        ("Max Drawdown", "15%", BLUE),
        ("Max Daily Loss", "2%", BLUE),
        ("Leverage Cap", "2.0x", BLUE),
        ("Critical Alerts", "0", GREEN),
        ("Router Gate", "strict", ACCENT),
    ]
    x, y = 90, 170
    for i, (name, val, color) in enumerate(cards):
        _draw_metric_box(draw, x, y, name, val, color)
        x += 380
        if (i + 1) % 3 == 0:
            x = 90
            y += 170
    _save(img, "risk_controls.png")


def make_canary_progress() -> None:
    img, draw = _canvas("Canary Ramp Progress", "Policy-driven capital progression states")
    draw.rounded_rectangle((120, 220, 1160, 320), radius=50, fill=CARD, outline=(48, 70, 110), width=2)
    steps = [0.05, 0.10, 0.15, 0.25, 0.40]
    x = 180
    for idx, step in enumerate(steps):
        color = GREEN if idx < 2 else MUTED
        draw.ellipse((x - 18, 252, x + 18, 288), fill=color)
        draw.text((x - 22, 300), f"{int(step*100)}%", fill=TEXT)
        if idx < len(steps) - 1:
            draw.line((x + 20, 270, x + 180, 270), fill=(52, 82, 130), width=6)
        x += 200
    draw.text((140, 380), "Current state: HOLD at 10% allocation (ops/risk gates enforced)", fill=ACCENT)
    _save(img, "canary_progress.png")


def make_ops_health() -> None:
    img, draw = _canvas("Ops Health Summary", "SLO, reconciliation, and incident posture")
    _draw_metric_box(draw, 100, 180, "SLO Breaches", "0 critical / 0 warning", GREEN)
    _draw_metric_box(draw, 500, 180, "Reconciliation Mismatch", "0", GREEN)
    _draw_metric_box(draw, 900, 180, "Incidents (60m)", "0", GREEN)
    _draw_metric_box(draw, 100, 360, "Stream Health", "healthy", BLUE)
    _draw_metric_box(draw, 500, 360, "TCA Drift Alerts", "0", GREEN)
    _draw_metric_box(draw, 900, 360, "Error Budget", "within threshold", ACCENT)
    _save(img, "ops_health.png")


def make_execution_pipeline() -> None:
    img, draw = _canvas("Execution Pipeline", "Signal -> Router -> Adapter -> Ledger -> Telemetry")
    stages = ["Signals", "Risk Router", "Exchange Adapter", "Order Ledger", "Telemetry"]
    x = 120
    for stage in stages:
        draw.rounded_rectangle((x, 290, x + 190, 390), radius=14, fill=CARD, outline=(48, 70, 110), width=2)
        draw.text((x + 20, 332), stage, fill=TEXT)
        if stage != stages[-1]:
            draw.polygon([(x + 202, 340), (x + 230, 322), (x + 230, 358)], fill=ACCENT)
        x += 220
    _save(img, "execution_pipeline.png")


def make_architecture_layers() -> None:
    img, draw = _canvas("Architecture Layers", "FastAPI backend + Next.js frontend + Streamlit internal ops")
    layers = [
        ("Next.js Web App", 120, 170, BLUE),
        ("FastAPI Service", 120, 290, ACCENT),
        ("PQTS Core (src/*)", 120, 410, GREEN),
        ("Postgres + Redis", 120, 530, MUTED),
    ]
    for text, x, y, color in layers:
        draw.rounded_rectangle((x, y, 1160, y + 90), radius=14, fill=CARD, outline=(48, 70, 110), width=2)
        draw.text((160, y + 34), text, fill=color)
    _save(img, "architecture_layers.png")


def make_performance_snapshot() -> None:
    row = {}
    bundles = _bundles()
    if bundles:
        csv_files = sorted(bundles[0].glob("simulation_leaderboard_*.csv"))
        if csv_files:
            row = _first_csv_row(csv_files[0])
    quality = float(row.get("avg_quality_score", 0.0) or 0.0)
    fill = float(row.get("avg_fill_rate", 0.0) or 0.0)
    reject = float(row.get("avg_reject_rate", 0.0) or 0.0)

    img, draw = _canvas("Performance Snapshot", "Public reproducible baseline metrics")
    draw.line((150, 580, 1100, 580), fill=(60, 86, 132), width=3)
    bars = [("Quality", quality, GREEN), ("Fill", fill, BLUE), ("Reject", reject, RED)]
    x = 280
    for label, value, color in bars:
        h = int(max(0.0, min(1.0, value)) * 340)
        draw.rectangle((x, 580 - h, x + 120, 580), fill=color)
        draw.text((x + 18, 595), label, fill=TEXT)
        draw.text((x + 32, 580 - h - 30), f"{value:.2f}", fill=TEXT)
        x += 220
    _save(img, "performance_snapshot.png")


def _gif_frames(label: str, color: tuple[int, int, int]) -> list[Image.Image]:
    frames: list[Image.Image] = []
    for i in range(12):
        img, draw = _canvas(label, "Generated preview animation")
        alpha = 60 + (i % 6) * 30
        pulse = (min(255, color[0] + alpha), min(255, color[1] + alpha), min(255, color[2] + alpha))
        draw.rounded_rectangle((220, 240, 1060, 500), radius=24, fill=CARD, outline=(48, 70, 110), width=2)
        draw.ellipse((500 - i * 4, 300 - i * 4, 780 + i * 4, 580 + i * 4), outline=pulse, width=8)
        draw.text((520, 360), "LIVE", fill=pulse)
        draw.text((520, 410), f"frame {i+1}", fill=TEXT)
        frames.append(img)
    return frames


def _save_gif(frames: Iterable[Image.Image], name: str) -> None:
    frames = list(frames)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        MEDIA_DIR / name,
        save_all=True,
        append_images=frames[1:],
        duration=120,
        loop=0,
    )


def make_gifs() -> None:
    _save_gif(_gif_frames("Dashboard Pulse", BLUE), "dashboard_pulse.gif")
    _save_gif(_gif_frames("Leaderboard Cycle", ACCENT), "leaderboard_cycle.gif")
    _save_gif(_gif_frames("Risk Alert Flash", RED), "risk_alert_flash.gif")


def main() -> int:
    make_dashboard_overview()
    make_simulation_leaderboard()
    make_risk_controls()
    make_canary_progress()
    make_ops_health()
    make_execution_pipeline()
    make_architecture_layers()
    make_performance_snapshot()
    make_gifs()
    print(f"Generated media in {MEDIA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
