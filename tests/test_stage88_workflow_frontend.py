from pathlib import Path
from qmt_ai_trading.console_api.task_registry import get_task

def test_stage88_workflow_frontend_assets_and_task():
    html=Path('local_console_app_stage88/index.html').read_text(encoding='utf-8')
    for text in ['真实行情缓存','Data Hub 质量','因子研究','候选池排名','策略信号','TradeIntent dry-run','Risk Gate']:
        assert text in html
    assert get_task('stage88_real_data_dry_run') is not None
