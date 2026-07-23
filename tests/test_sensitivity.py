"""
Unit tests for downside risk and weight sensitivity analysis (sensitivity.py).
"""

from pathlib import Path
import pytest
import pandas as pd
from src.modeling.sensitivity import run_sensitivity_analysis

SAMPLE_CSV_PATH = Path("data/sample/stock_prices.sample.csv")


def test_run_sensitivity_analysis_basic(tmp_path):
    """Verify that sensitivity runs combinations and writes result files to output directory."""
    holdings = [
        {"ticker": "005930", "quantity": 70, "average_price": 75000},
        {"ticker": "000660", "quantity": 30, "average_price": 180000}
    ]

    summary = run_sensitivity_analysis(
        holdings=holdings,
        price_data=SAMPLE_CSV_PATH,
        esg_input=None,  # Will use default/mock ESG risk scores
        output_dir=tmp_path,
        data_mode="sample"
    )

    assert summary["total_runs"] > 0
    assert summary["successful_runs"] > 0
    assert (tmp_path / "sensitivity_results.csv").exists()
    assert (tmp_path / "sensitivity_summary.json").exists()

    df_results = pd.read_csv(tmp_path / "sensitivity_results.csv")
    assert "rec_weight_samsung" in df_results.columns
    assert "optimized_total_risk" in df_results.columns
