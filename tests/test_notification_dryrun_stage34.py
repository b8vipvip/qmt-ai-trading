import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.notification_dryrun.models import *
from qmt_ai_trading.notification_dryrun.safety import *
from qmt_ai_trading.notification_dryrun.templates import build_daily_pipeline_summary_message, build_monitoring_alert_message
from qmt_ai_trading.notification_dryrun.planner import build_recipients_from_config, build_delivery_plans
from qmt_ai_trading.notification_dryrun.audit import audit_delivery_plans
from qmt_ai_trading.notification_dryrun.formatters import format_notification_dry_run_markdown
from qmt_ai_trading.notification_dryrun.service import run_notification_dry_run
from qmt_ai_trading.dashboard.safety import build_default_dashboard_config
from qmt_ai_trading.dashboard.collector import collect_notification_dry_run_section

SAFETY='Notification dry-run does not send real messages, does not call external networks, and does not read real tokens.'

def test_models_and_safety():
    m=NotificationMessage(subject='hello', body='body')
    r=NotificationRecipient(destination_masked=mask_destination('ops@example.com'))
    p=NotificationDeliveryPlan(recipient=r,message=m)
    assert m.to_dict()['subject']=='hello'
    assert 'ops@example.com' not in r.destination_masked
    assert p.dry_run and not p.real_send_enabled and not p.external_network_enabled
    for s in ['token=abc','api_key=abc','password=x','secret=y','account=1','Bearer abcdef','sk-abcdefghi']:
        assert contains_sensitive_secret(s)
    for s in ['real send','smtp','requests.post','telegram bot sendMessage','wechat webhook','urllib']:
        assert contains_real_send_action(s)
    p.real_send_enabled=True
    assert not validate_delivery_plan_safety(p)['passed']

def test_templates_planner_audit_format():
    m1=build_daily_pipeline_summary_message({'ok': True})
    m2=build_monitoring_alert_message('warning')
    recipients=build_recipients_from_config('ops@example.com,telegram:123456,wechat:https://example.invalid/webhook',['EMAIL','TELEGRAM','WECHAT'])
    plans=build_delivery_plans([m1,m2],recipients)
    assert all(not p.real_send_enabled and not p.external_network_enabled for p in plans)
    assert any(str(p.send_mode).endswith('SUPPRESSED') or getattr(p.send_mode,'value',None)=='SUPPRESSED' for p in plans)
    audit=audit_delivery_plans(plans)
    assert audit.passed
    report=NotificationDryRunReport(messages=[m1],recipients=recipients,delivery_plans=plans,audit_result=audit)
    assert SAFETY in format_notification_dry_run_markdown(report)

def test_cli_and_dashboard(tmp_path):
    md=tmp_path/'out.md'; js=tmp_path/'out.json'; prev=tmp_path/'previews'
    code=subprocess.run([sys.executable,'scripts/run_notification_dry_run.py','--channels','FILE,CONSOLE,EMAIL,TELEGRAM,WECHAT','--recipients','ops@example.com,telegram:123456','--output',str(md),'--json-output',str(js),'--preview-output-dir',str(prev)],check=False,capture_output=True,text=True)
    assert code.returncode==0, code.stderr
    assert md.exists() and js.exists()
    data=json.loads(js.read_text())
    assert all(not p['real_send_enabled'] and not p['external_network_enabled'] for p in data['delivery_plans'])
    cfg=build_default_dashboard_config(notification_dry_run_dir=str(tmp_path), include_notification_dry_run=True)
    sec=collect_notification_dry_run_section(cfg)
    assert sec.status.value=='OK'

def test_daily_and_register_notification_args(tmp_path):
    out=tmp_path/'ndr'
    code=subprocess.run([sys.executable,'scripts/run_daily_pipeline.py','--data-source-mode','legacy','--enable-notification-dry-run','--notification-dry-run-output-dir',str(out),'--notification-dry-run-channels','FILE,EMAIL'],capture_output=True,text=True)
    assert code.returncode==0, code.stderr
    assert 'Notification Dry Run' in code.stdout
    reg=subprocess.run([sys.executable,'scripts/register_daily_pipeline_task.py','--enable-notification-dry-run','--notification-dry-run-output-dir','notification_dryrun','--notification-dry-run-channels','FILE,CONSOLE,EMAIL'],capture_output=True,text=True)
    assert reg.returncode==0, reg.stderr
    assert '--enable-notification-dry-run' in reg.stdout and '--notification-dry-run-channels' in reg.stdout

def test_gitignore_and_roadmap_and_sync_untouched():
    gi=Path('.gitignore').read_text(encoding='utf-8')
    assert 'notification_dryrun/' in gi or 'notification_dryrun_stage34/' in gi
    road=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '阶段三十四' in road and '真实通知 dry-run 接入准备' in road
    assert '阶段三十五' in road and '小资金灰度人工流程演练' in road
