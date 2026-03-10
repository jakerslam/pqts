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

#[pymodule]
fn pqts_hotpath(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(sum_notional, m)?)?;
    Ok(())
}
