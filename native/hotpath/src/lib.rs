use pyo3::prelude::*;

#[pyfunction]
fn version() -> String {
    "pqts_hotpath 0.1.0".to_string()
}

#[pymodule]
fn pqts_hotpath(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    Ok(())
}
