from __future__ import annotations

from .common import payload, read_json


def _preview_doc():
    data = read_json('portfolio', 'order_preview_latest.json', {})
    return data if isinstance(data, dict) else {}


def _budget_doc():
    data = read_json('portfolio', 'portfolio_budget.json', {})
    return data if isinstance(data, dict) else {}


def status():
    preview = _preview_doc()
    budget = _budget_doc()
    budget_body = budget.get('budget') if isinstance(budget.get('budget'), dict) else {}
    return payload(
        status=preview.get('status') or budget.get('status') or 'DATA_MISSING',
        preview_count=len(preview.get('previews', [])) if isinstance(preview.get('previews'), list) else 0,
        blocked_count=budget_body.get('blocked_count', 0),
        cash=budget_body.get('cash'),
        total_asset=budget_body.get('total_asset'),
        market_value=budget_body.get('market_value'),
        position_count=budget_body.get('position_count'),
        preview_only=True,
        can_submit_order=False,
        source_path=preview.get('source_path', 'artifacts/reports/console/portfolio/order_preview_latest.json'),
    )


def preview():
    data = _preview_doc()
    if not data or data.get('status') == 'DATA_MISSING':
        return payload(status='DATA_MISSING', previews=[], empty_reason='真实订单预览产物不存在，请先运行 order_preview_dry_run。', preview_only=True, can_submit_order=False)
    return payload(
        status=data.get('status', 'READY'),
        previews=data.get('previews', []),
        preview_only=True,
        can_submit_order=False,
        source_path=data.get('source_path', 'artifacts/reports/console/portfolio/order_preview_latest.json'),
    )


def budget():
    data = _budget_doc()
    if not data or data.get('status') == 'DATA_MISSING':
        return payload(status='DATA_MISSING', budget={}, empty_reason='资金预算产物不存在，请先运行 order_preview_dry_run。', preview_only=True, can_submit_order=False)
    return payload(
        status=data.get('status', 'READY'),
        budget=data.get('budget', {}),
        preview_only=True,
        can_submit_order=False,
        source_path=data.get('source_path', 'artifacts/reports/console/portfolio/portfolio_budget.json'),
    )
