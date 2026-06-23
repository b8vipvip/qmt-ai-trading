from .common import payload, read_json


def _latest():
    data = read_json('account_readonly', 'account_readonly_report.json', {})
    if not isinstance(data, dict):
        data = {}
    report = data.get('report') if isinstance(data.get('report'), dict) else {}
    nested_report = report.get('report') if isinstance(report.get('report'), dict) else {}
    diagnostics = nested_report.get('account_readonly_diagnostics') if isinstance(nested_report.get('account_readonly_diagnostics'), dict) else {}
    status_doc = nested_report.get('account_readonly_status') if isinstance(nested_report.get('account_readonly_status'), dict) else {}
    return data, report, nested_report, diagnostics, status_doc


def _fallback_status():
    return payload(
        status='MANUAL_CONFIRM_REQUIRED',
        enabled=False,
        account_id_masked='***MASKED***',
        mode='isolated_subprocess',
        safety_status='MANUAL_CONFIRM_REQUIRED',
        account_query_enabled=False,
        position_query_enabled=False,
        position_count=0,
    )


def status():
    data, report, nested_report, diagnostics, status_doc = _latest()
    if not report or data.get('status') in {'DATA_MISSING', 'DATA_ERROR'}:
        return _fallback_status()
    return payload(
        status=report.get('status') or status_doc.get('status') or data.get('status') or 'READY',
        enabled=bool(report.get('enabled') or status_doc.get('enabled')),
        mode=report.get('mode') or 'isolated_subprocess',
        account_id_masked=diagnostics.get('account_id_masked') or report.get('account_id') or '***MASKED***',
        account_query_enabled=bool(report.get('account_query_enabled') or status_doc.get('account_query_enabled')),
        position_query_enabled=bool(report.get('position_query_enabled') or status_doc.get('position_query_enabled')),
        position_count=report.get('position_count', nested_report.get('position_count', 0)),
        safety_status=nested_report.get('safety_status') or diagnostics.get('safety_status') or status_doc.get('safety_status') or 'READONLY_ENABLED',
        mock_data=bool(report.get('mock_data', False)),
        last_connect_result=report.get('last_connect_result') or diagnostics.get('connect_result'),
        connect_status=diagnostics.get('connect_status'),
        trader_started=diagnostics.get('trader_started'),
        xttrader_imported=diagnostics.get('xttrader_imported'),
        timeout_seconds=report.get('timeout_seconds'),
        source_path=data.get('source_path', 'artifacts/reports/console/account_readonly/account_readonly_report.json'),
    )


def diagnostics():
    data, report, nested_report, diagnostics_doc, status_doc = _latest()
    if not report or data.get('status') in {'DATA_MISSING', 'DATA_ERROR'}:
        return payload(diagnostics=data, account_id='***MASKED***', status=data.get('status', 'MANUAL_CONFIRM_REQUIRED'))
    return payload(
        status=report.get('status') or 'READY',
        diagnostics=diagnostics_doc or nested_report or report,
        account_id='***MASKED***',
        account_id_masked=diagnostics_doc.get('account_id_masked', '***MASKED***') if isinstance(diagnostics_doc, dict) else '***MASKED***',
    )


def asset():
    data, report, nested_report, diagnostics_doc, status_doc = _latest()
    if not report or data.get('status') in {'DATA_MISSING', 'DATA_ERROR'}:
        return payload(status='MANUAL_CONFIRM_REQUIRED', asset={}, account_id='***MASKED***')
    asset_doc = report.get('asset') if isinstance(report.get('asset'), dict) else {}
    return payload(
        status=report.get('status') or 'READY',
        enabled=bool(report.get('enabled')),
        account_query_enabled=bool(report.get('account_query_enabled')),
        account_id='***MASKED***',
        account_id_masked=diagnostics_doc.get('account_id_masked', '***MASKED***') if isinstance(diagnostics_doc, dict) else '***MASKED***',
        asset=asset_doc,
        total_asset=asset_doc.get('total_asset') or asset_doc.get('m_dTotalAsset'),
        cash=asset_doc.get('cash') or asset_doc.get('m_dCash'),
        market_value=asset_doc.get('market_value') or asset_doc.get('m_dMarketValue'),
        mock_data=bool(report.get('mock_data', False)),
    )


def positions():
    data, report, nested_report, diagnostics_doc, status_doc = _latest()
    if not report or data.get('status') in {'DATA_MISSING', 'DATA_ERROR'}:
        return payload(status='MANUAL_CONFIRM_REQUIRED', positions=[], account_id='***MASKED***')
    pos_doc = report.get('positions')
    if isinstance(pos_doc, dict):
        pos_list = pos_doc.get('positions', [])
        pos_count = pos_doc.get('position_count', len(pos_list) if isinstance(pos_list, list) else 0)
    elif isinstance(pos_doc, list):
        pos_list = pos_doc
        pos_count = len(pos_list)
    else:
        pos_list = []
        pos_count = report.get('position_count', 0)
    return payload(
        status=report.get('status') or 'READY',
        enabled=bool(report.get('enabled')),
        position_query_enabled=bool(report.get('position_query_enabled')),
        position_count=pos_count,
        positions=pos_list,
        account_id='***MASKED***',
        account_id_masked=diagnostics_doc.get('account_id_masked', '***MASKED***') if isinstance(diagnostics_doc, dict) else '***MASKED***',
        mock_data=bool(report.get('mock_data', False)),
    )
