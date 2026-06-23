from __future__ import annotations
from typing import Any
from pathlib import Path
from .account_readonly_config import AccountReadonlyConfig, mask_account_for_config
from .account_masking import mask_payload
from .account_rate_limit import AccountReadonlyRateLimiter

ERRORS={
 'path_missing':'CONFIG_ERROR_USERDATA_PATH_MISSING','path_not_exists':'CONFIG_ERROR_USERDATA_PATH_NOT_EXISTS','account_missing':'CONFIG_ERROR_ACCOUNT_ID_MISSING','import':'IMPORT_ERROR_XTTRADER','connect':'CONNECT_ERROR','asset':'ACCOUNT_QUERY_ERROR','positions':'POSITION_QUERY_ERROR','start':'XTTRADER_START_ERROR'}

class AccountReadonlyProvider:
    def __init__(self, config: AccountReadonlyConfig | None = None, trader: Any = None, account: Any = None, rate_limiter: AccountReadonlyRateLimiter | None = None):
        self.config=config or AccountReadonlyConfig(); self.trader=trader; self.account=account; self.rate_limiter=rate_limiter or AccountReadonlyRateLimiter(self.config.max_queries_per_minute); self._connect_result=None; self._import_error=''; self._started=False; self._start_result=None
    def _base_diag(self):
        p=Path(self.config.userdata_mini_path) if self.config.userdata_mini_path else None
        return {'ok':True,'config_source':self.config.config_source,'repo_root':self.config.repo_root,'userdata_mini_path_configured':bool(self.config.userdata_mini_path),'userdata_mini_path_exists':bool(p and p.exists()),'account_configured':bool(self.config.account_id),'account_id_masked':mask_account_for_config(self.config.account_id),'account_type':self.config.account_type,'session_id':self.config.session_id,'xttrader_imported':False,'trader_started':self._started,'start_result':self._start_result,'connect_attempted':False,'connect_result':self._connect_result,'connect_status':'NOT_ATTEMPTED','read_only':True,'order_submit_enabled':False,'order_cancel_enabled':False,'real_order_submitted':False}
    def get_status(self) -> dict:
        enabled=bool(self.config.enabled and self.config.read_only and self.config.dry_run and self.config.manual_confirmation_completed)
        status='MANUAL_CONFIRM_REQUIRED' if self.config.enabled and not self.config.manual_confirmation_completed else ('SUCCESS' if enabled else 'DISABLED')
        return {'ok':True,'status':status,'enabled':enabled,'account_query_enabled':enabled and self.config.allow_account_query,'position_query_enabled':enabled and self.config.allow_position_query,'order_submit_enabled':False,'order_cancel_enabled':False,'real_order_submitted':False,'safety_status':'MANUAL_CONFIRM_REQUIRED' if self.config.enabled and not self.config.manual_confirmation_completed else ('READONLY_ENABLED' if enabled else 'DISABLED_FOR_SAFETY'),'mock_data':not enabled,'read_only':True,'dry_run':True,'requires_human_approval':True,'manual_confirmation_completed':bool(self.config.manual_confirmation_completed),'account_masked':True}
    def _error(self, code, message, **extra):
        d={**self.get_status(), **self._base_diag(), 'ok':False,'status':code,'error_code':code,'error_message':message,'mock_data':False,'no_order_submitted':True}; d.update(extra); return d
    def diagnostics(self, query_kind=None):
        d={**self.get_status(), **self._base_diag()}
        if not self.config.userdata_mini_path: return self._error(ERRORS['path_missing'],'QMT_USERDATA_MINI_PATH/QMT_USERDATA_PATH is missing')
        if not d['userdata_mini_path_exists']: return self._error(ERRORS['path_not_exists'],'configured userdata_mini path does not exist')
        if not self.config.account_id: return self._error(ERRORS['account_missing'],'QMT_ACCOUNT_ID is missing')
        if not self.config.allow_import_xttrader: return d
        if self.trader is not None:
            d['xttrader_imported']=True
        else:
            try:
                self._import_xttrader_classes(); d['xttrader_imported']=True
            except Exception as exc:
                return self._error(ERRORS['import'],str(exc),xttrader_imported=False)
        if self.config.allow_connect_trade_session:
            cr=self._ensure_real_client(connect=True); return {**self.get_status(), **self._base_diag(), 'ok': cr==0, 'xttrader_imported':True, 'trader_started':self._started, 'connect_attempted':True, 'connect_result':cr, 'connect_status':'SUCCESS' if cr==0 else 'FAILED', **({} if cr==0 else {'status':ERRORS['connect'],'error_code':ERRORS['connect'],'error_message':'MiniQMT connect_result != 0'})}
        d['xttrader_imported']=True; return d
    def _import_xttrader_classes(self):
        from xtquant.xttrader import XtQuantTrader
        from xtquant.xttype import StockAccount
        return XtQuantTrader, StockAccount
    def _ensure_started(self):
        if self.trader is None or self._started:
            return
        start_fn=getattr(self.trader, 'start', None)
        if callable(start_fn):
            self._start_result=start_fn()
        else:
            self._start_result='NO_START_METHOD'
        self._started=True
    def _ensure_real_client(self, connect=False):
        if self.trader is not None:
            self._ensure_started()
            if connect and self._connect_result is None and hasattr(self.trader, 'connect'):
                self._connect_result=self.trader.connect()
            return self._connect_result if self._connect_result is not None else 0
        XtQuantTrader, StockAccount = self._import_xttrader_classes()
        self.trader=XtQuantTrader(self.config.userdata_mini_path, self.config.session_id)
        self.account=StockAccount(self.config.account_id, self.config.account_type)
        self._ensure_started()
        if connect:
            self._connect_result=self.trader.connect()
            return self._connect_result
        return 0
    def _blocked(self, gate): return {**self.get_status(),'gate':gate,'query_attempted':False,'message':'account readonly query disabled by safety gate'}
    def query_account_asset(self):
        if not (self.config.enabled and self.config.read_only and self.config.manual_confirmation_completed and self.config.allow_account_query): return self._blocked('account_asset')
        limited=self.rate_limiter.allow()
        if limited['status']!='PASS': return limited
        diag=self.diagnostics('asset') if self.trader is None else {'ok': True}
        if diag.get('ok') is False: return diag if diag.get('error_code') != ERRORS['connect'] else diag
        try:
            self._ensure_real_client(connect=False); fn=getattr(self.trader,'query_stock_asset',None) or getattr(self.trader,'query_asset',None); data=fn(self.account) if self.account is not None else fn()
        except Exception as exc: return self._error(ERRORS['asset'],str(exc))
        return {**self.get_status(), **self._base_diag(),'ok':True,'status':'SUCCESS','mock_data':False,'account_masked':True,'asset':mask_payload(data),'no_order_submitted':True}
    def query_positions(self):
        if not (self.config.enabled and self.config.read_only and self.config.manual_confirmation_completed and self.config.allow_position_query): return self._blocked('positions')
        limited=self.rate_limiter.allow()
        if limited['status']!='PASS': return limited
        diag=self.diagnostics('positions') if self.trader is None else {'ok': True}
        if diag.get('ok') is False: return diag
        try:
            self._ensure_real_client(connect=False); fn=getattr(self.trader,'query_stock_positions',None) or getattr(self.trader,'query_positions',None); data=fn(self.account) if self.account is not None else fn(); data=data if isinstance(data,list) else list(data or [])
        except Exception as exc: return self._error(ERRORS['positions'],str(exc))
        return {**self.get_status(), **self._base_diag(),'ok':True,'status':'SUCCESS','mock_data':False,'account_masked':True,'positions':mask_payload(data),'position_count':len(data),'no_order_submitted':True}
