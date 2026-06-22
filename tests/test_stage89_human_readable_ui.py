from pathlib import Path
from qmt_ai_trading.paper_trading.report import run_paper_trading_stage89


def test_stage89_outputs_human_readable_summaries(tmp_path):
    status=run_paper_trading_stage89('.',88,str(tmp_path/'out'),True,True)
    assert status['paper_fill_count']==2
    orders=(tmp_path/'out'/'paper_orders.json').read_text(encoding='utf-8')
    fills=(tmp_path/'out'/'paper_fills.json').read_text(encoding='utf-8')
    assert 'paper_order_summary' in orders and '保持观望' in orders and '策略建议 HOLD' in orders and 'SKIPPED' in orders
    assert 'paper_fill_summary' in fills and 'NO_FILL' in fills


def test_stage89_frontend_uses_human_readable_main_view():
    html=Path('local_console_app_stage89/index.html').read_text(encoding='utf-8')
    for label in ['标的','操作','数量','参考价','模拟成交价','状态','风控','原因','资金总览','Shadow PnL 指标卡','Risk Replay 风控复核','保持观望','不操作']:
        assert label in html
    assert "pnlbox.innerHTML='<pre>'" not in html
    assert "risk.innerHTML='<pre>'" not in html
    assert '查看详情' in html and '高级调试：Shadow PnL 原始 JSON' in html
