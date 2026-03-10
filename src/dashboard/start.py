#!/usr/bin/env python3
"""Start the Dash-based PQTS operator dashboard."""

from __future__ import annotations

from dashboard.app import app


def start_dashboard() -> None:
    print("Starting PQTS dashboard (Dash)...")
    print("Dashboard URL: http://localhost:8501")
    app.run(host="0.0.0.0", port=8501, debug=False)


if __name__ == "__main__":
    start_dashboard()
