use pyo3::prelude::*;

#[pyfunction]
fn version() -> String {
    "pqts_hotpath 0.1.0".to_string()
}

#[pyfunction]
fn sum_notional(levels: Vec<(f64, f64)>, max_levels: usize) -> f64 {
    let mut total: f64 = 0.0;
    let limit = if max_levels == 0 { 1 } else { max_levels };
    for (idx, (price, size)) in levels.iter().enumerate() {
        if idx >= limit {
            break;
        }
        let p = if *price > 0.0 { *price } else { 0.0 };
        let q = if *size > 0.0 { *size } else { 0.0 };
        total += p * q;
    }
    total
}

#[pyfunction]
fn fill_metrics(
    side: &str,
    reference_price: f64,
    executed_price: f64,
    requested_qty: f64,
    executed_qty: f64,
) -> (f64, f64) {
    let ref_denom = if reference_price > 1e-12 {
        reference_price
    } else {
        1e-12
    };
    let side_token = side.to_ascii_lowercase();
    let slip_pct = if side_token == "buy" {
        ((executed_price - reference_price) / ref_denom).max(0.0)
    } else {
        ((reference_price - executed_price) / ref_denom).max(0.0)
    };
    let req_denom = if requested_qty > 1e-12 {
        requested_qty
    } else {
        1e-12
    };
    (slip_pct * 10000.0, executed_qty / req_denom)
}

#[pyfunction]
fn sequence_transition(
    expected_sequence: Option<i64>,
    received_sequence: i64,
    allow_auto_recover: bool,
    snapshot_sequence: Option<i64>,
) -> (String, i64, i64, bool, Option<i64>, i64) {
    match expected_sequence {
        None => {
            let next_expected = received_sequence + 1;
            (
                "seed".to_string(),
                next_expected,
                0,
                false,
                None,
                next_expected,
            )
        }
        Some(expected) => {
            if received_sequence < expected {
                ("stale_drop".to_string(), expected, 0, false, None, expected)
            } else if received_sequence == expected {
                (
                    "in_order".to_string(),
                    expected,
                    0,
                    false,
                    None,
                    received_sequence + 1,
                )
            } else {
                let gap_size = received_sequence - expected;
                if allow_auto_recover {
                    if let Some(snapshot) = snapshot_sequence {
                        let next_expected = snapshot + 1;
                        return (
                            "gap_recovered_snapshot".to_string(),
                            expected,
                            gap_size,
                            true,
                            Some(snapshot),
                            next_expected,
                        );
                    }
                }
                (
                    "gap_detected".to_string(),
                    expected,
                    gap_size,
                    false,
                    None,
                    expected,
                )
            }
        }
    }
}

#[pymodule]
fn pqts_hotpath(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(sum_notional, m)?)?;
    m.add_function(wrap_pyfunction!(fill_metrics, m)?)?;
    m.add_function(wrap_pyfunction!(sequence_transition, m)?)?;
    Ok(())
}
