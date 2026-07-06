from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import TaskRun
from qmt_ai_trading.common.json_safe import json_safe


DEFAULT_HISTORY_PATH = Path('artifacts/reports/console/task_history/task_history.json')


class TaskStore:
    def __init__(self, history_path: str | Path | None = DEFAULT_HISTORY_PATH, max_persisted_runs: int = 1000):
        self.runs: dict[str, TaskRun] = {}
        self.path = Path(history_path) if history_path else None
        self.max_persisted_runs = max_persisted_runs
        self.load_error: str | None = None
        self.last_persist_error: str | None = None
        self._loading = False
        self._persisting = False
        self._load()

    @property
    def history_mode(self):
        return 'persistent_json_file' if self.path else 'in_memory_current_api_process'

    @property
    def history_path(self):
        return str(self.path) if self.path else None

    def _attach(self, run: TaskRun):
        object.__setattr__(run, '_store', self)
        return run

    def _coerce_run(self, item: dict[str, Any]):
        run = TaskRun(
            run_id=str(item.get('run_id') or ''),
            task_id=str(item.get('task_id') or ''),
            task_name=str(item.get('task_name') or item.get('task_id') or ''),
            category=str(item.get('category') or ''),
            status=str(item.get('status') or 'UNKNOWN'),
            params=item.get('params') if isinstance(item.get('params'), dict) else {},
            started_at=item.get('started_at'),
            finished_at=item.get('finished_at'),
            logs=item.get('logs') if isinstance(item.get('logs'), list) else [],
            output=item.get('output') if isinstance(item.get('output'), dict) else {},
            output_artifacts=item.get('output_artifacts') if isinstance(item.get('output_artifacts'), list) else [],
        )
        return self._attach(run)

    def _load(self):
        if not self.path or not self.path.exists():
            return
        self._loading = True
        try:
            raw = json.loads(self.path.read_text(encoding='utf-8'))
            if isinstance(raw, dict):
                items = raw.get('runs', [])
            elif isinstance(raw, list):
                items = raw
            else:
                items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                run = self._coerce_run(item)
                if run.run_id:
                    self.runs[run.run_id] = run
        except Exception as exc:
            self.load_error = str(exc)
            self.runs = {}
        finally:
            self._loading = False

    def _trim(self):
        if not self.max_persisted_runs or len(self.runs) <= self.max_persisted_runs:
            return
        items = list(self.runs.values())[-self.max_persisted_runs:]
        self.runs = {r.run_id: self._attach(r) for r in items}

    def _persist(self):
        if not self.path or self._loading or self._persisting:
            return
        self._persisting = True
        try:
            self._trim()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'history_mode': self.history_mode,
                'runs': [json_safe(r.to_dict()) for r in self.runs.values()],
            }
            tmp = self.path.with_suffix(self.path.suffix + '.tmp')
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            tmp.replace(self.path)
            self.last_persist_error = None
        except Exception as exc:
            self.last_persist_error = str(exc)
        finally:
            self._persisting = False

    def add(self, run: TaskRun):
        self.runs[run.run_id] = self._attach(run)
        self._persist()
        return run

    def save(self, run: TaskRun | None = None):
        if run is not None:
            self.runs[run.run_id] = self._attach(run)
        self._persist()
        return run

    def get(self, rid):
        self._persist()
        return self.runs.get(rid)

    def list(self, limit=None):
        self._persist()
        items = list(reversed(list(self.runs.values())))
        if limit is None:
            return items
        try:
            n = max(0, int(limit))
        except Exception:
            n = 50
        return items[:n]
