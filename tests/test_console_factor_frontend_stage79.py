from pathlib import Path
ROOT=Path('local_console_app_stage79')
def read(n): return (ROOT/n).read_text(encoding='utf-8')

def test_frontend_factor_menu_and_panels():
    html=read('index.html'); js=read('app.js')
    for x in ['总览','行情数据','AI 模型配置','因子研究','选股中心','策略任务','Agent 投研','回测分析','风控中心','报告中心','任务中心','系统设置']:
        assert x in html or x in js
    for x in ['因子列表表格','因子配置面板','因子运行面板','IC','RankIC','候选池排名','run factor_scan','factor values','composite_score','risk_flags']:
        assert x in js

def test_factor_frontend_apis_and_no_danger_fetch():
    js=read('app.js')
    for p in ['/factors/catalog','/factors/config','/factors/results','/factors/evaluation','/factors/candidates','/tasks/run']:
        assert p in js
    for bad in ['xttrader','XtQuantTrader','query_stock_asset','query_stock_positions','place_order','submit_order','自动 approve',"fetch('/trade')",'fetch("/account")']:
        assert bad not in js
