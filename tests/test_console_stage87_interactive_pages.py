from pathlib import Path

APP = Path('local_console_app_stage87')
JS = (APP / 'app.js').read_text(encoding='utf-8')
HTML = (APP / 'index.html').read_text(encoding='utf-8')


def test_stage87_app_is_cumulative_and_keeps_stage77_to_86_entries():
    required = ['总览','行情数据','因子研究','选股中心','策略任务','Agent 投研','AI 模型配置','回测分析','风控中心','报告中心','任务中心','系统设置','xtdata 只读行情','artifacts 迁移']
    for label in required:
        assert label in JS
    assert 'Stage87 控制台' in HTML


def test_existing_backend_modules_are_not_static_placeholders():
    interactive = ['factor','backtest','risk','marketReplay','xtBoundary','xtLive','artifacts']
    for module_id in interactive:
        marker = "id:'%s'" % module_id
        start = JS.index(marker)
        chunk = JS[start:start+450]
        assert "status:'INTERACTIVE'" in chunk
        assert "apis:[" in chunk


def test_interactive_pages_have_required_ui_states():
    for text in ['刷新','运行 dry-run 任务','加载中','API_ERROR','数据来源','原始 JSON 折叠查看区','空数据提示','fallback/mock_data']:
        assert text in JS


def test_specific_stage_api_fetch_logic_present():
    expected = [
        '/api/v1/factor/candidates/latest',
        '/api/v1/backtest/report/latest',
        '/api/v1/backtest/performance/latest',
        '/api/v1/monitoring/alerts/latest',
        '/api/v1/market/sandbox/report/latest',
        '/api/v1/xtdata-live/status',
        '/api/v1/artifacts/migration/report',
    ]
    for api in expected:
        assert api in JS
