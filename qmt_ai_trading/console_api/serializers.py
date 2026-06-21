from dataclasses import asdict
def task_to_dict(t): return asdict(t)
def run_to_dict(r): return r.to_dict()
