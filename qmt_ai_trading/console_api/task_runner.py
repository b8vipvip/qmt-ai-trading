from __future__ import annotations
import uuid
from .models import TaskRun, now_iso
from .task_registry import get_task
from .safety import *
def mock_output(task_id, params):
    base={'mode':'dry-run/shadow','no_trade_authorization':True,'read_only':True,'params':params}
    if task_id in {'ai_model_discovery','ai_model_stress_test','ai_model_usage_draft'}: base.update({'ai_provider_task':True,'local_api_only':True,'trade_chain':False,'note':'Stage78 AI Provider 白名单任务，仅调用本地 Console API，不进入交易链路'})
    elif task_id=='market_snapshot_readonly': base.update({'symbol':params.get('symbol','510300.SH'),'source':'local readonly/mock','ohlcv':{'open':3.91,'high':3.96,'low':3.88,'close':3.94,'volume':1200000},'quality':'OK'})
    elif task_id.startswith('agent_'): base.update({'advice':'HOLD','confidence':0.62,'reasons':['结构化建议，仅供人工复核'],'risk_flags':['实盘关闭','不得自动下单']})
    elif 'risk' in task_id or 'blockers' in task_id: base.update({'blocked':True,'blockers':['实盘未启用','缺少人工审批','Stage77 仅 dry-run']})
    elif 'backtest' in task_id or 'replay' in task_id: base.update({'total_return':0.032,'max_drawdown':0.041,'win_rate':0.55,'trade_count':12})
    else: base.update({'candidates':[{'symbol':'510300.SH','rank':1,'score':82,'reasons':['动量稳定'],'risk_flags':['dry-run']}], 'signals':[{'symbol':'159915.SZ','signal':'HOLD','trade_intent':'DRY_RUN_ONLY'}]})
    return base
def run_task(task_id, params, store):
    assert_safe_task_id(task_id); assert_safe_task_params(params)
    task=get_task(task_id)
    if not task: raise ConsoleSafetyError('未知任务，不在白名单')
    assert_task_allowed(task); assert_no_forbidden_live_task(task)
    run=TaskRun(str(uuid.uuid4()),task.task_id,task.title_zh,task.category,'RUNNING', {**task.default_params, **params}, now_iso())
    store.add(run); run.logs.append('任务已通过白名单与安全边界校验'); run.logs.append('以 dry-run / shadow / read-only 模式执行')
    run.output=mock_output(task_id, run.params); run.output_artifacts=task.output_artifacts; run.status='SUCCESS'; run.finished_at=now_iso(); run.logs.append('任务完成：未下单、未查账户、未自动批准')
    return run
