from qmt_ai_trading.console_api.workflow_console import workflow_status, dry_run_check, write_workflow_outputs


def test_workflow_status_api_shape_covers_main_architecture():
    data = workflow_status('.')
    layers = [x['layer'] for x in data['workflow']]
    for expected in ['QMT Gateway / xtdata','Data Hub','Research / Qlib factors','TradingAgents','Strategy Engine','Risk Gate','Human Approval','Paper Trading / Shadow Trading']:
        assert expected in layers
    assert data['dry_run'] is True
    assert data['no_order_submitted'] is True
    assert any(x['status'] == 'BACKEND_MISSING' for x in data['workflow'])
    assert next(x for x in data['workflow'] if x['layer'] == 'Live Trading')['status'] == 'DISABLED'


def test_workflow_dry_run_outputs_are_readonly(tmp_path):
    result = write_workflow_outputs('.', tmp_path.as_posix())
    assert result['status'] == 'SUCCESS'
    assert (tmp_path / 'workflow_status.json').exists()
    assert (tmp_path / 'workflow_feature_matrix.md').exists()
    assert dry_run_check('.')['no_xttrader'] is True
