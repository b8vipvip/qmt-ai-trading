from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from typing import Any, Mapping

RUNTIME_DIR = "local_runtime_account_stage91"

_SAFE = {
    "read_only": True,
    "order_submit_enabled": False,
    "order_cancel_enabled": False,
    "real_order_submitted": False,
    "allow_order_submit": False,
    "allow_order_cancel": False,
}

_ENV_KEYS = ["QMT_USERDATA_MINI_PATH", "QMT_USERDATA_PATH", "QMT_ACCOUNT_ID", "QMT_ACCOUNT_TYPE", "QMT_SESSION_ID_BASE"]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"data": data}
    except Exception as exc:
        return {"json_read_error": str(exc), "path": str(path)}


def _mask_account(account_id: Any) -> str:
    s = "" if account_id is None else str(account_id)
    return "" if not s else ("****" if len(s) < 6 else f"{s[:2]}****{s[-2:]}")


def _success_payload(output_dir: Path) -> dict[str, Any]:
    report = _read_json(output_dir / "account_readonly_report.json")
    asset = _read_json(output_dir / "account_asset_snapshot.json")
    positions = _read_json(output_dir / "account_positions_snapshot.json")
    asset_obj = asset.get("asset", asset if "total_asset" in asset else {})
    pos_list = positions.get("positions", [])
    if isinstance(pos_list, dict):
        pos_list = pos_list.get("positions", [])
    if not isinstance(pos_list, list):
        pos_list = []
    return {
        "ok": True,
        "status": "SUCCESS",
        "enabled": True,
        "manual_confirmation_completed": True,
        "account_query_enabled": True,
        "position_query_enabled": True,
        "account_masked": True,
        "mock_data": False,
        "asset": asset_obj,
        "position_count": positions.get("position_count", len(pos_list)),
        "positions": pos_list,
        "report": report,
        "last_runtime_status": report.get("status") or asset.get("status") or positions.get("status"),
        "last_connect_result": asset.get("connect_result", positions.get("connect_result")),
        **_SAFE,
    }


def run_account_readonly_subprocess(repo_root: str | Path, request_params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    request_params = request_params or {}
    output_dir = root / RUNTIME_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(root / "scripts" / "run_account_readonly_stage91.py"),
        "--repo-root", str(root), "--output-dir", RUNTIME_DIR,
        "--enable-account-readonly", "--allow-import-xttrader", "--allow-connect-trade-session",
        "--allow-account-query", "--allow-position-query", "--manual-confirmed", "--read-only", "--dry-run",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    for key in _ENV_KEYS:
        val = request_params.get(key)
        if isinstance(val, (list, tuple)):
            val = val[0] if val else None
        if val not in (None, ""):
            env[key] = str(val)
    completed = subprocess.run(cmd, cwd=str(root), env=env, text=True, capture_output=True, timeout=120)
    if completed.returncode != 0:
        return {"ok": False, "status": "SUBPROCESS_QUERY_FAILED", "error_message": (completed.stderr or completed.stdout or "account readonly subprocess failed")[-2000:], "returncode": completed.returncode, "enabled": True, "manual_confirmation_completed": True, "account_query_enabled": True, "position_query_enabled": True, "mock_data": False, **_SAFE}
    payload = _success_payload(output_dir)
    if not (output_dir / "account_readonly_report.json").exists():
        return {"ok": False, "status": "SUBPROCESS_QUERY_FAILED", "error_message": "account_readonly_report.json was not produced", "stdout_tail": completed.stdout[-1000:], "enabled": True, "manual_confirmation_completed": True, "account_query_enabled": True, "position_query_enabled": True, "mock_data": False, **_SAFE}
    return payload


def format_asset_response(result: Mapping[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        return dict(result)
    return {k: result.get(k) for k in ["ok", "status", "enabled", "manual_confirmation_completed", "account_query_enabled", "position_query_enabled", "account_masked", "mock_data", "asset", "order_submit_enabled", "order_cancel_enabled", "real_order_submitted", "read_only"]}


def format_positions_response(result: Mapping[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        return dict(result)
    return {k: result.get(k) for k in ["ok", "status", "enabled", "manual_confirmation_completed", "position_count", "positions", "account_masked", "order_submit_enabled", "order_cancel_enabled", "real_order_submitted", "read_only"]}
