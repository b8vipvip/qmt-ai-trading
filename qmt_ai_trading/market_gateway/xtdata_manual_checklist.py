from __future__ import annotations
from dataclasses import dataclass, asdict

LABELS = [
'我确认当前阶段不会连接真实行情','我确认当前阶段不会调用 xttrader','我确认当前阶段不会查询账户','我确认当前阶段不会下单','我确认 xtdata import 默认关闭','我确认 MiniQMT 连接默认关闭','我确认 real_market_data 默认关闭','我确认 sandbox fallback 保持开启','我确认真实启用必须进入后续阶段','我确认本阶段只生成 dry-run 报告']
@dataclass(frozen=True)
class ChecklistItem:
    check_id: str; label: str; required: bool=True; checked: bool=False; blocking_if_unchecked: bool=True
    def to_dict(self): return asdict(self)
@dataclass(frozen=True)
class XtDataManualChecklist:
    items: tuple
    checklist_status: str='REQUIRES_HUMAN_REVIEW'
    manual_confirmation_completed: bool=False
    def to_dict(self): return {'items':[i.to_dict() for i in self.items], 'checklist_status':self.checklist_status, 'manual_confirmation_completed':self.manual_confirmation_completed}
def default_manual_checklist(): return XtDataManualChecklist(tuple(ChecklistItem(f'CHK-{i:02d}', label) for i,label in enumerate(LABELS,1)))
