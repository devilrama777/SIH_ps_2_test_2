"""
Unit tests for EnvironmentVerifier.
Phase 12 (Section 38 & 39).
"""
import sys
from pathlib import Path

import pytest

from installer.verify_environment import CheckResult, EnvironmentDiagnosticReport, EnvironmentVerifier


def test_python_version_check():
    verifier = EnvironmentVerifier()
    res = verifier.check_python_version()
    assert isinstance(res, CheckResult)
    assert res.name == "python_version"
    assert res.passed is True
    assert "Python 3." in res.details


def test_memory_check():
    verifier = EnvironmentVerifier()
    res = verifier.check_memory()
    assert isinstance(res, CheckResult)
    assert res.name == "system_memory"
    assert "RAM" in res.details


def test_disk_space_check(tmp_path: Path):
    verifier = EnvironmentVerifier(base_dir=tmp_path)
    res = verifier.check_disk_space()
    assert isinstance(res, CheckResult)
    assert res.name == "disk_space"
    assert "Free Disk Space:" in res.details


def test_sqlite_fts5_check():
    verifier = EnvironmentVerifier()
    res = verifier.check_sqlite_fts5()
    assert isinstance(res, CheckResult)
    assert res.name == "sqlite_fts5"
    assert res.passed is True
    assert "FTS5" in res.details


def test_workspace_directories_check(tmp_path: Path):
    verifier = EnvironmentVerifier(base_dir=tmp_path)
    res = verifier.check_workspace_directories()
    assert isinstance(res, CheckResult)
    assert res.passed is True
    assert (tmp_path / "data" / "workspace").exists()
    assert (tmp_path / "data" / "indexes").exists()
    assert (tmp_path / "data" / "cache").exists()
    assert (tmp_path / "models" / "cache").exists()


def test_document_libraries_check():
    verifier = EnvironmentVerifier()
    res = verifier.check_document_libraries()
    assert isinstance(res, CheckResult)
    assert res.passed is True


def test_local_model_cache_check(tmp_path: Path):
    verifier = EnvironmentVerifier(base_dir=tmp_path)
    res = verifier.check_local_model_cache()
    assert isinstance(res, CheckResult)
    assert res.name == "local_model_cache"
    assert res.passed is True


def test_loopback_security_check():
    verifier = EnvironmentVerifier()
    res = verifier.check_loopback_binding_security()
    assert isinstance(res, CheckResult)
    assert res.passed is True
    assert "127.0.0.1" in res.details


def test_run_all_checks(tmp_path: Path):
    verifier = EnvironmentVerifier(base_dir=tmp_path)
    report = verifier.run_all_checks()
    assert isinstance(report, EnvironmentDiagnosticReport)
    assert report.overall_status is True
    assert len(report.checks) == 8
    assert report.system_os != ""
    assert report.python_version == sys.version.split()[0]
