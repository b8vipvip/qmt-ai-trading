from .common import payload, read_json
def status(): return payload(status='MANUAL_CONFIRM_REQUIRED', enabled=False, account_id_masked='***MASKED***', mode='isolated_subprocess')
def diagnostics(): return payload(diagnostics=read_json('account_readonly','account_readonly_report.json',{}), account_id='***MASKED***')
def asset(): return payload(status='MANUAL_CONFIRM_REQUIRED', asset={}, account_id='***MASKED***')
def positions(): return payload(status='MANUAL_CONFIRM_REQUIRED', positions=[], account_id='***MASKED***')
