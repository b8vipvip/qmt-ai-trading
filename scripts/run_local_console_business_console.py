from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.console_api.task_registry import list_tasks
from qmt_ai_trading.console_api.serializers import task_to_dict

def write(p,s): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding='utf-8')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--output-dir',default='local_console_app_stage77'); ap.add_argument('--closure-dir',default='local_console_closure_stage75'); ap.add_argument('--roadmap-dir',default='stage76_roadmap_review'); a=ap.parse_args()
    out=Path(a.repo_root)/a.output_dir; out.mkdir(exist_ok=True)
    tasks=[task_to_dict(t) for t in list_tasks()]
    write(out/'task_catalog.md', '# Stage77 任务白名单\n\n'+'\n'.join(f"- `{t['task_id']}`：{t['title_zh']} / {t['category']} / dry-run={t['dry_run_only']}" for t in tasks))
    write(out/'frontend_api_contract.md','# 前后端 API 契约\n\nGET /api/v1/health；GET /api/v1/tasks/catalog；POST /api/v1/tasks/run；GET /api/v1/tasks；GET /api/v1/tasks/{task_id}；GET /api/v1/tasks/{task_id}/logs；GET /api/v1/reports；GET /api/v1/market/snapshot；GET /api/v1/console/summary。\n')
    md='# Stage77 业务控制台 MVP 报告\n\nStage77 从开发验收台纠偏为本地业务控制台 MVP。前端可触发白名单 dry-run 任务、查看状态、日志摘要和报告摘要；仍不接实盘、不查账户、不下单、不调用 xttrader、不自动 approve。\n'
    write(out/'local_console_business_console_report.md',md)
    write(out/'local_console_business_console_report.json', json.dumps({'stage':77,'name':'业务控制台 MVP 与任务编排 API 层','tasks':len(tasks),'no_trade_authorization':True},ensure_ascii=False,indent=2))
    write(out/'integration_check_report.md','# 联调检查报告\n\n- API host 固定 127.0.0.1。\n- 前端调用白名单 API。\n- POST 仅 /api/v1/tasks/run。\n- 禁止任意命令、敏感路径、实盘接口。\n')
    write(out/'next_pre_live_safety_audit_plan.md','# Stage78 预告\n\n阶段七十八：实盘前安全审计重启与真实数据质量复核层。仍然不是实盘。\n')
if __name__=='__main__': main()
