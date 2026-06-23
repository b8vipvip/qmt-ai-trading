from .common import payload, read_json


def status():
    data = read_json('approval', 'approval_status.json', {'status': 'MANUAL_REVIEW_ONLY', 'approval': {}})
    approval = data.get('approval', data) if isinstance(data, dict) else {}
    return payload(
        status=approval.get('status', 'MANUAL_REVIEW_ONLY') if isinstance(approval, dict) else 'MANUAL_REVIEW_ONLY',
        approval_enabled=False,
        approve_in_console=False,
        auto_approve=False,
        real_order_submitted=False,
        no_order_submitted=True,
        approval=approval,
        cli_hint='Console only generates manual review cards; it never approves live trading.',
    )


def requests():
    data = read_json('approval', 'approval_requests.json', {'status': 'READY_EMPTY', 'requests': []})
    reqs = data.get('requests', []) if isinstance(data, dict) else []
    return payload(status=data.get('status', 'READY_EMPTY') if isinstance(data, dict) else 'READY_EMPTY', requests=reqs)
