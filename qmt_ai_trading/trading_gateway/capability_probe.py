from .xttrader_config import default_xttrader_boundary_config
from .xttrader_boundary import XtTraderBoundaryAdapter

def run_capability_probe(config=None):
    adapter = XtTraderBoundaryAdapter(config or default_xttrader_boundary_config())
    return {"status":"DISABLED","safety_status":"DISABLED_FOR_SAFETY","import_probe":adapter.probe_import(),"connection_probe":adapter.probe_connection(),"account_query_probe":adapter.probe_account_query(),"order_submit_probe":adapter.probe_order_submit(),"blocked_by_safety":True,"dry_run":True,"read_only":True}
