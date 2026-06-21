from pathlib import Path
from qmt_ai_trading.agents_research.safety import validate_agent_output, validate_report

def test_agent_safety_blocks_forbidden_terms():
    out=validate_agent_output({'summary':'please execute_order now','risk_flags':[],'research_only':True})
    assert out['unsafe'] is True
    assert any('unsafe_agent_output_blocked' in f for f in out['risk_flags'])

def test_validate_stage81_readonly_constraints():
    text=Path('scripts/validate_stage81.ps1').read_text(encoding='utf-8')
    assert 'Set-Content' not in text and 'Add-Content' not in text and 'Out-File' not in text
    assert 'install_run_qmt_tasks_logging.ps1' not in text
    assert 'D:\\AI\\run_qmt_tasks.ps1' in text

def test_final_report_safety_flags():
    report=validate_report({'summary':'safe research only','warnings':[]})
    assert report['dry_run'] and report['not_live_trading'] and report['research_only']
