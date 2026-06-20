from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GITIGNORE_RULES = ("__pycache__/", "*.pyc", "*.pyo", ".pytest_cache/")
CACHE_PATTERNS = ("__pycache__", "*.pyc", "*.pyo")


def test_gitignore_covers_python_cache_artifacts() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    lines = {line.strip() for line in text.splitlines()}
    for rule in REQUIRED_GITIGNORE_RULES:
        assert rule in lines


def test_stage63_and_later_validators_clean_python_cache_before_final_sync() -> None:
    validators = sorted((ROOT / "scripts").glob("validate_stage*.ps1"))
    stage63_plus = [path for path in validators if _stage_number(path) >= 63]
    for path in stage63_plus:
        text = path.read_text(encoding="utf-8")
        assert "function Clean-PythonCache" in text, f"{path} must define Clean-PythonCache locally"
        assert text.count("Clean-PythonCache") >= 2, f"{path} must invoke Clean-PythonCache"
        for pattern in CACHE_PATTERNS:
            assert pattern in text, f"{path} must clean {pattern}"
        clean_index = text.rfind("Clean-PythonCache")
        scan_index = text.rfind('"-Mode","scan"')
        if scan_index == -1:
            scan_index = text.rfind("-Mode scan")
        status_index = text.rfind('"-Mode","status"')
        if status_index == -1:
            status_index = text.rfind("-Mode status")
        assert scan_index != -1, f"{path} must run sync_all.ps1 -Mode scan"
        assert status_index != -1, f"{path} must run sync_all.ps1 -Mode status"
        assert clean_index < scan_index < status_index, f"{path} must clean cache before final sync scan/status"


def _stage_number(path: Path) -> int:
    stem = path.stem
    return int(stem.removeprefix("validate_stage"))
