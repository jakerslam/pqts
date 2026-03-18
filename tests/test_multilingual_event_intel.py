from __future__ import annotations

import pytest

from execution.multilingual_event_intel import (
    build_event_extraction_payload,
    evaluate_translation_gate,
    normalize_multilingual_event,
)


def test_normalize_multilingual_event_and_payload_roundtrip() -> None:
    record = normalize_multilingual_event(
        event_id="evt-1",
        source_ref="source://telegram/post/1",
        original_language="ru",
        original_text="Порт загружен танкерами",
        translated_text="Port is loaded with tankers",
        translation_method="nmt_v2",
        translation_confidence=0.88,
        translation_timestamp="2026-03-18T00:00:00+00:00",
    )
    payload = build_event_extraction_payload(record)
    assert payload["event_id"] == "evt-1"
    assert payload["original_language"] == "ru"
    assert payload["original_text"] == "Порт загружен танкерами"
    assert payload["translated_text"] == "Port is loaded with tankers"
    assert payload["translation_confidence"] == pytest.approx(0.88)


def test_translation_gate_policy_actions() -> None:
    high = normalize_multilingual_event(
        event_id="evt-allow",
        source_ref="source://x/1",
        original_language="es",
        original_text="Cambio en suministro",
        translated_text="Supply change",
        translation_method="nmt_v2",
        translation_confidence=0.92,
    )
    medium = normalize_multilingual_event(
        event_id="evt-down-rank",
        source_ref="source://x/2",
        original_language="es",
        original_text="Posible retraso",
        translated_text="Possible delay",
        translation_method="nmt_v2",
        translation_confidence=0.60,
    )
    low = normalize_multilingual_event(
        event_id="evt-block",
        source_ref="source://x/3",
        original_language="es",
        original_text="Frase ambigua",
        translated_text="Ambiguous phrase",
        translation_method="nmt_v2",
        translation_confidence=0.30,
    )
    assert evaluate_translation_gate(high) == ("allow", ())
    assert evaluate_translation_gate(medium) == ("down_rank", ("translation_confidence_marginal",))
    assert evaluate_translation_gate(low) == ("block", ("translation_confidence_too_low",))
