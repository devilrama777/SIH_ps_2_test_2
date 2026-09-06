"""
Tests for NumericalValidator — Section 17 deterministic mathematical validation.
"""
from core.validation.numerical import NumericalValidator, ValidationIssue


def test_percentage_sum_valid():
    validator = NumericalValidator()
    text = "Coal evacuation by mode: Rail: 62.0%, Road: 23.0%, MGR: 15.0%."
    issues = validator.validate_section("sec_01", text, [])
    # Should have no percentage warnings since 62 + 23 + 15 = 100.0%
    pct_issues = [i for i in issues if "Percentage distribution sum anomaly" in i.message]
    assert len(pct_issues) == 0


def test_percentage_sum_anomaly():
    validator = NumericalValidator()
    text = "Distribution of transport: Rail: 70.0%, Road: 20.0%, MGR: 18.0%."
    # 70 + 20 + 18 = 108%
    issues = validator.validate_section("sec_01", text, [])
    pct_issues = [i for i in issues if "Percentage distribution sum anomaly" in i.message]
    assert len(pct_issues) == 1
    assert pct_issues[0].severity == "warning"


def test_unit_consistency_warning():
    validator = NumericalValidator()
    text = "Total raw coal production reached 45.2 MT and 1000000 tonnes elsewhere."
    issues = validator.validate_section("sec_02", text, [])
    unit_issues = [i for i in issues if "Unit inconsistency detected" in i.message]
    assert len(unit_issues) == 1
