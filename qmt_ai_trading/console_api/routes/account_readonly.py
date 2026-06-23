from __future__ import annotations

import json
from pathlib import Path

from .common import payload, read_json

RUNTIME_DIR = Path('local_runtime_account_stage91')


def _read_runtime_json(name: str) -> dict:
    path = RUNTIME_DIR / name
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        return data if isinstance(data, dict) else {'items': data}
    except Exception as exc:
        return {'status': 'DATA_ERROR', 'error': str(exc), 'source_path': path.as_posix()}


def _latest():
    data = read_json('account_readonly', 'account_readonly_report.json', {})
    if not isinstance(data, dict):
        data = {}
    report = data.get('report') if isinstance(data.get('report'), dict) else {}
    nested_report = report.get('report') if isinstance(report.get('report'), dict) else {}
    diagnostics = nested_report.get('account_readonly_diagnostics') if isinstance(nested_report.get('account_readonly_diagnostics'), dict) else {}
    status_doc = nested_report.get('account_readonly_status') if isinstance(nested_report.get('account_readonly_status'), dict) else {}

    runtime_asset = _read_runtime_json('account_asset_snapshot.json')
    runtime_positions = _read_runtime_json('account_positions_snapshot.json')
    runtime_report = _read_runtime_json('account_readonly_report.json')

    runtime_success = runtime_asset.get('status') == 'SUCCESS' or runtime_positions.get('status') == 'SUCCESS' or runtime_report.get('status') == 'SUCCESS'
    console_looks_disabled = (not report) or report.get('status') == 'DISABLED' or (report.get('enabled') is False and not report.get('asset'))
    if runtime_success and console_looks_disabled:
        asset = runtime_asset.get('asset') if isinstance(runtime_asset.get('asset'), dict) else {}
        positions = runtime_positions.get('positions', []) if isinstance(runtime_positions.get('positions'), list) else []
        position_count = runtime_positions.get('position_count', len(positions))
        fallback_report = {
            'ok': True,
            'status': 'SUCCESS',
            'mode': 'isolated_subprocess',
            'enabled': True,
            'manual_confirmation_completed': True,
            'account_query_enabled': True,
            'position_query_enabled': True,
            'account_masked': True,
            'mock_data': False,
            'asset': asset,
            'position_count': position_count,
            'positions': {'position_count': position_count, 'positions': positions},
            'last_runtime_status': 'SUCCESS',
            'last_connect_result': runtime_asset.get('connect_result', runtime_positions.get('connect_result')),
            'read_only': True,
            'order_submit_enabled': False,
            'order_cancel_enabled': False,
            'real_order_submitted': False,
            'allow_order_submit': False,
            'allow_order_cancel': False,
            'no_order_submitted': True,
            'source_path': RUNTIME_DIR.as_posix(),
        }
        runtime_diag = {k: runtime_asset.get(k, runtime_positions.get(k)) for k in [
            'account_id_masked', 'account_type', 'config_source', 'connect_result', 'connect_status',
            'session_id', 'start_result', 'trader_started', 'userdata_mini_path_configured',
            'userdata_mini_path_exists', 'xttrader_imported', 'safety_status'
        ]}
        data = {'status': 'SUCCESS', 'report': fallback_report, 'source_path': RUNTIME_DIR.as_posix()}
        report = fallback_report
        nested_report = fallback_report
        diagnostics = runtime_diag
        status_doc = fallback_report

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
