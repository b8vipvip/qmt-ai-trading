from __future__ import annotations
from typing import Any
FORBIDDEN_TERMS=("execute_order","live_trade","auto_approve","bypass_risk","xttrader","place_order","buy_now","sell_now")
def scan_text(text:str)->list[str]:
    low=text.lower(); return [t for t in FORBIDDEN_TERMS if t in low]
def validate_agent_output(output:dict[str,Any])->dict[str,Any]:
    hits=scan_text(str(output)); flags=list(output.get('risk_flags') or [])
    unsafe=bool(hits)
    if unsafe: flags.append('unsafe_agent_output_blocked:'+','.join(hits))
    if not output.get('research_only', True): unsafe=True; flags.append('missing_research_only')
    output={**output,'risk_flags':flags,'dry_run':True,'not_live_trading':True,'research_only':True,'unsafe':unsafe}
    return output
def validate_report(report:dict[str,Any])->dict[str,Any]:
    hits=scan_text(str(report)); warnings=list(report.get('warnings') or [])
    if hits: warnings.append('final_report_blocked_for_unsafe_terms:'+','.join(hits))
    report['warnings']=warnings; report['blocked']=bool(hits) or bool(report.get('blocked'))
    report['not_live_trading']=True; report['dry_run']=True; report['research_only']=True
    return report
