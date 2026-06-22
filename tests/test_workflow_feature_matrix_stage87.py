from qmt_ai_trading.console_api.workflow_console import feature_matrix


def test_feature_matrix_covers_required_features_and_safety_statuses():
    data = feature_matrix('.')
    by_name = {x['feature']: x for x in data['features']}
    required = ['QMT Gateway / xtdata','QMT Gateway / xttrader account query','QMT Gateway / order submit','Data Hub / symbols','Data Hub / market cache','Research / factors','TradingAgents / technical','Strategy Engine / multi-factor stock','Risk Gate / trade validator','Human Approval','Paper Trading','Shadow Trading','Live Trading']
    for name in required:
        assert name in by_name
    assert by_name['QMT Gateway / xttrader account query']['status'] == 'DISABLED_FOR_SAFETY'
    assert by_name['QMT Gateway / order submit']['status'] == 'DISABLED_FOR_SAFETY'
    assert by_name['Live Trading']['status'] == 'DISABLED_FOR_SAFETY'
    assert by_name['Data Hub / symbols']['status'] == 'BACKEND_MISSING'
    assert by_name['Research / factors']['status'] == 'INTERACTIVE'
