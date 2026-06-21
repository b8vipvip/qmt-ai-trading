from __future__ import annotations
from .models import TaskRun
class TaskStore:
    def __init__(self): self.runs={}
    def add(self, run:TaskRun): self.runs[run.run_id]=run; return run
    def get(self, rid): return self.runs.get(rid)
    def list(self): return list(reversed(list(self.runs.values())))
