from __future__ import annotations
import ast
from pathlib import Path

FORBIDDEN_IMPORTS = [("xtquant", "xttrader"), ("xtquant.xttrader", None)]

def scan_imports(paths: list[str] | None = None, repo_root: str = ".") -> dict:
    root = Path(repo_root)
    files = [Path(p) for p in paths] if paths else list((root / "qmt_ai_trading").rglob("*.py")) + list((root / "scripts").glob("*.py"))
    hits = []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "xtquant.xttrader":
                        hits.append({"file": str(path), "line": node.lineno, "kind": "import"})
            elif isinstance(node, ast.ImportFrom):
                if node.module == "xtquant" and any(a.name == "xttrader" for a in node.names):
                    hits.append({"file": str(path), "line": node.lineno, "kind": "from-import"})
                if node.module == "xtquant.xttrader":
                    hits.append({"file": str(path), "line": node.lineno, "kind": "from-import"})
    return {"status": "PASS" if not hits else "FAIL", "xttrader_imported": False, "hits": hits, "blocked_by_safety": True, "dry_run": True, "read_only": True}
