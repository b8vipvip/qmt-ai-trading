from __future__ import annotations
from .alert_builder import make_alert
from .safety import scan_obj, CRITICAL_TERMS, ACCOUNT_TERMS
RULES=['MISSING_INPUT_FILE','FALLBACK_USED','MOCK_DATA_USED','UNSAFE_AGENT_OUTPUT','FORBIDDEN_TERM_DETECTED','HIGH_DRAWDOWN','LOW_WIN_RATE','RISK_GATE_BYPASS_ATTEMPT','AUTO_APPROVE_DETECTED','LIVE_TRADE_TERM_DETECTED','QMT_TRADER_API_DETECTED','ORDER_SUBMIT_DETECTED','ACCOUNT_QUERY_DETECTED','DIRTY_REPO_STATUS','VALIDATION_LOG_ENCODING_ERROR']

def _walk(obj, key):
    if isinstance(obj,dict):
        if key in obj: yield obj[key]
        for v in obj.values(): yield from _walk(v,key)
    elif isinstance(obj,list):
        for v in obj: yield from _walk(v,key)

def detect_alerts(ctx, drawdown_threshold=0.2, win_rate_threshold=0.35):
    alerts=[]; ts=ctx['created_at']
    for rel in ctx.get('missing_files',[]):
        alerts.append(make_alert('MISSING_INPUT_FILE','WARNING','Stage80/81/82',rel,'输入文件缺失，已启用安全 fallback。',{'fallback_used':True,'mock_data':True},'补齐上游 dry-run 输出；不得升级为实盘依据。',ts))
    for s in ctx['input_sources']:
        if s['fallback_used']: alerts.append(make_alert('FALLBACK_USED','INFO',s['stage'],s['path'],'检测到 fallback_used=true。',s,'保持 dry-run，并复核上游数据完整性。',ts))
        if s['mock_data']: alerts.append(make_alert('MOCK_DATA_USED','WARNING',s['stage'],s['path'],'检测到 mock_data=true。',s,'仅用于研究和前端联调。',ts))
    for rel,obj in ctx['payloads'].items():
        stage=next((s['stage'] for s in ctx['input_sources'] if s['path']==rel),'Stage80/81/82')
        if any(v is True for v in _walk(obj,'unsafe')):
            alerts.append(make_alert('UNSAFE_AGENT_OUTPUT','CRITICAL',stage,rel,'检测到 unsafe=true。',{'unsafe':True},'立即 dry-run 熔断并人工复核。',ts))
        for term in scan_obj(obj):
            sev='CRITICAL' if term in CRITICAL_TERMS else 'HIGH'
            rule='FORBIDDEN_TERM_DETECTED'
            if term=='auto_approve': rule='AUTO_APPROVE_DETECTED'
            elif term in {'live_trade'}: rule='LIVE_TRADE_TERM_DETECTED'
            elif term in {'xttrader','XtQuantTrader'}: rule='QMT_TRADER_API_DETECTED'
            elif term in {'execute_order','place_order','buy_now','sell_now'}: rule='ORDER_SUBMIT_DETECTED'
            elif term in ACCOUNT_TERMS: rule='ACCOUNT_QUERY_DETECTED'
            elif term=='bypass_risk': rule='RISK_GATE_BYPASS_ATTEMPT'
            alerts.append(make_alert(rule,sev,stage,rel,f'检测到禁止项：{term}。',{'term':term},'保持 dry-run 阻断；删除危险项并人工复核。',ts))
        for dd in _walk(obj,'max_drawdown'):
            try:
                if float(dd)>drawdown_threshold: alerts.append(make_alert('HIGH_DRAWDOWN','HIGH',stage,rel,'max_drawdown 超阈值。',{'max_drawdown':dd,'threshold':drawdown_threshold},'暂停后续执行，仅研究复盘。',ts))
            except Exception: pass
        for wr in _walk(obj,'win_rate'):
            try:
                if float(wr)<win_rate_threshold: alerts.append(make_alert('LOW_WIN_RATE','WARNING',stage,rel,'win_rate 低于阈值。',{'win_rate':wr,'threshold':win_rate_threshold},'复核策略有效性。',ts))
            except Exception: pass
        for key,rule in [('not_live_trading','LIVE_TRADE_TERM_DETECTED'),('research_only','RISK_GATE_BYPASS_ATTEMPT'),('no_qmt_trader_api','QMT_TRADER_API_DETECTED'),('no_order_submitted','ORDER_SUBMIT_DETECTED')]:
            if any(v is False for v in _walk(obj,key)):
                alerts.append(make_alert(rule,'CRITICAL',stage,rel,f'{key}=false，触发安全告警。',{key:False},'强制保持 dry-run 并人工复核。',ts))
    if ctx.get('repo_dirty'):
        alerts.append(make_alert('DIRTY_REPO_STATUS','WARNING','Stage83','git status','检测到 Git 工作区 Dirty=True。',{'repo_dirty':True},'提交或清理本阶段输出，确保幂等。',ts))
    for f in ctx.get('validation_nul_logs',[]):
        alerts.append(make_alert('VALIDATION_LOG_ENCODING_ERROR','HIGH','Stage83',f,'validation log 含 NUL 空字符。',{'nul':True},'重新生成无 NUL 验证日志。',ts))
    return alerts
