import json
import pytest
from pathlib import Path
from core.evaluation.golden_dataset import GoldenDatasetBuilder


def test_golden_dataset_generation(tmp_path):
    builder = GoldenDatasetBuilder(base_dir=str(tmp_path))
    out_dir = builder.build_dataset()

    assert out_dir.exists()
    assert (out_dir / "digital_pages" / "CCL_Annual_Report_FY24_Highlights.txt").exists()
    assert (
        (out_dir / "financial_tables" / "CCL_Production_Offtake_FY24.xlsx").exists()
        or (out_dir / "financial_tables" / "CCL_Production_Offtake_FY24.csv").exists()
    )
    assert (
        (out_dir / "csr_sections" / "CSR_Community_Development_FY24.docx").exists()
        or (out_dir / "csr_sections" / "CSR_Community_Development_FY24.txt").exists()
    )
    assert (out_dir / "audit_sections" / "CAG_Audit_Compliance_FY24.txt").exists()
    assert (out_dir / "ground_truth.json").exists()

    # Verify ground truth structure
    gt = json.loads((out_dir / "ground_truth.json").read_text(encoding="utf-8"))
    assert gt["subsidiary_name"] == "Central Coalfields Limited"
    assert gt["key_metrics"]["raw_coal_production_fy24_mt"] == 84.50
    assert gt["key_metrics"]["production_growth_percent"] == 9.03
