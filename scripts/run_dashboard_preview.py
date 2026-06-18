#!/usr/bin/env python
"""Preview a read-only dashboard path or serve its directory with stdlib http.server."""

from __future__ import annotations

import argparse
import functools
import http.server
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.dashboard.service import preview_dashboard_path


class ReadOnlyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        self.send_error(405, "Read-only dashboard server")

    def do_PUT(self) -> None:  # noqa: N802
        self.send_error(405, "Read-only dashboard server")

    def do_DELETE(self) -> None:  # noqa: N802
        self.send_error(405, "Read-only dashboard server")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview read-only dashboard output.")
    parser.add_argument("--dashboard", default="dashboard_stage31/index.html")
    parser.add_argument("--print-path-only", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    dashboard = Path(args.dashboard).resolve()
    print(preview_dashboard_path(dashboard))
    if not args.serve:
        return 0
    directory = dashboard.parent
    handler = functools.partial(ReadOnlyHandler, directory=str(directory))
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Serving read-only dashboard directory {directory} at http://127.0.0.1:{args.port}/")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
