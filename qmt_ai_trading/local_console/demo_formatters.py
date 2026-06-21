from __future__ import annotations
import json
from .demo_models import *

def format_json_md(title, body): return f'# {title}\n\n```json\n{body}\n```\n'

def format_local_console_demo_package_report_md(r: LocalConsoleDemoPackageReport)->str:
    lines=['# Stage74 Local Demo Package Layer','','## Decision',r.decision.value,'','## Safety Note','本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。','READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW 只表示本地演示打包层材料可供人工复核。','demo guide / manifest / package index 都不是审批授权。','']
    sections=[('Evidence Summary',r.evidence),('Demo Home',r.demo_home),('Demo Manifest',r.demo_manifest),('Demo Guide',r.demo_guide),('Demo Route Map',r.demo_route_map),('Demo Asset Manifest',r.demo_asset_manifest),('Demo Package Index',r.demo_package_index),('Demo Safety Report',r.demo_safety_findings),('Demo Validation Summary',r.demo_validation_summary),('Forbidden Hash Routes',['#/order','#/orders','#/trade','#/execute','#/approve','#/approval','#/auto-approve','#/live','#/notify','#/account','#/positions','#/assets']),('Forbidden JS Actions',["fetch('/order')","fetch('/trade')","fetch('/approve')",'XMLHttpRequest','dangerous buttons']),('Stage73 Help Docs Evidence',[e for e in r.evidence if e.stage=='Stage73']),('Stage72 UI Acceptance Evidence',[e for e in r.evidence if e.stage=='Stage72']),('Stage71 Review Workbench Evidence',[e for e in r.evidence if e.stage=='Stage71']),('Stage70 Drilldown Evidence',[e for e in r.evidence if e.stage=='Stage70']),('Roadmap Stage Plan Evidence',['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。']),('UI Productization Plan Evidence',['Stage61-75 前端 UI 产品化计划继续保留，UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。']),('Required Manual Confirmations',['人工确认本地演示包只用于只读复核。']),('Blocking Reasons',r.blocking_reasons),('Warnings',r.warnings),('Encoding / UTF-8 Check',['Markdown/JSON 使用 UTF-8，ensure_ascii=False，不包含 NUL/U+FFFD/mojibake markers。'])]
    for title,obj in sections:
        lines += [f'## {title}', json.dumps(to_plain(obj),ensure_ascii=False,indent=2), '']
    lines += ['## Next Stage Preview','Stage75 进入 UI 产品化收口层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。','']
    return '\n'.join(lines)
