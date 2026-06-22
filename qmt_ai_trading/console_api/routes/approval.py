from .common import payload, read_json
def status(): return payload(status='MANUAL_REVIEW_ONLY', approval_enabled=False, approve_in_console=False, cli_hint='Use approval CLI manually; console never auto-approves live trading.')
def requests(): return payload(status='READY_EMPTY', requests=read_json('approval','approval_requests.json',{'requests':[]}).get('requests',[]))
