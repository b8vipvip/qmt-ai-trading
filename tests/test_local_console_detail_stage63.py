from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.local_console.detail_models import *
from qmt_ai_trading.local_console.detail_reader import read_latest_validation_detail, read_console_detail_json
from qmt_ai_trading.local_console.detail_service import *
from qmt_ai_trading.local_console.detail_formatters import format_detail_report_md
from qmt_ai_trading.local_console.safety import scan_local_console_detail_text_for_forbidden_markers


def _stage62(root, decision='READY_FOR_LOCAL_CONSOLE_REVIEW', critical=0):
    d=root/'local_console_stage62'; d.mkdir()
    (d/'local_console_report.json').write_text(json.dumps({'decision':decision,'summary':{'critical_count':critical},'warnings':[]},ensure_ascii=False),encoding='utf-8')

def test_config_and_default_report_construct():
    assert LocalConsoleDetailConfig().read_only is True
    assert LocalConsoleDetailReport().decision == LocalConsoleDetailDecision.NEED_MORE_EVIDENCE

def test_missing_stage62_needs_more_evidence(tmp_path):
    r=run_local_console_detail_review(LocalConsoleDetailConfig(repo_root=tmp_path))
    assert r.decision in {LocalConsoleDetailDecision.NEED_MORE_EVIDENCE, LocalConsoleDetailDecision.NO_GO}

def test_ready_and_no_go_decisions(tmp_path):
    _stage62(tmp_path)
    r=run_local_console_detail_review(LocalConsoleDetailConfig(repo_root=tmp_path))
    assert r.decision == LocalConsoleDetailDecision.READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW
    (tmp_path/'local_console_stage62'/'local_console_report.json').write_text(json.dumps({'decision':'NO_GO','summary':{'critical_count':1}}),encoding='utf-8')
    r=run_local_console_detail_review(LocalConsoleDetailConfig(repo_root=tmp_path))
    assert r.decision == LocalConsoleDetailDecision.NO_GO

def test_routes_and_filters(tmp_path):
    _stage62(tmp_path); r=run_local_console_detail_review(LocalConsoleDetailConfig(repo_root=tmp_path))
    for p in ['/dashboard/detail','/reports/detail']+[f'/reports/stage{i}/detail' for i in range(62,54,-1)]: assert p in r.route_index
    for k in ['stage','status','severity','warnings','blocking-reasons']: assert k in r.filter_index

def test_subreports_generate(tmp_path):
    _stage62(tmp_path); r=run_local_console_detail_review(LocalConsoleDetailConfig(repo_root=tmp_path))
    assert build_console_warnings_report(r) is not None
    assert build_console_blocking_reasons_report(r) is not None
    assert build_console_manifest_detail_report(r).items
    assert build_console_validation_detail_report(r) is not None

def test_validation_log_utf8_utf16_and_no_nul(tmp_path):
    d=tmp_path/'validation_logs'; d.mkdir()
    (d/'stage63_validation_1.log').write_text('hello utf8',encoding='utf-8')
    assert 'hello' in read_latest_validation_detail(d).summary
    (d/'stage63_validation_2.log').write_bytes('hello utf16'.encode('utf-16-le'))
    detail=read_latest_validation_detail(d)
    assert 'hello utf16' in detail.summary
    assert '\x00' not in detail.summary

def test_reader_blocks_sensitive(tmp_path):
    p=tmp_path/'.env'; p.write_text('{}')
    assert read_console_detail_json(p).status == LocalConsoleDetailStatus.FAIL
    for name in ['token.json','key.json','secret.json']:
        p=tmp_path/name; p.write_text('{}')
        assert read_console_detail_json(p).status == LocalConsoleDetailStatus.FAIL

def test_safety_marker_classification():
    assert scan_local_console_detail_text_for_forbidden_markers('不调用 xttrader','local_console_stage62/a.md',generated=True)[0]['severity']=='WARN'
    hits=scan_local_console_detail_text_for_forbidden_markers('XtQuantTrader place_order query_stock_asset','qmt_ai_trading/live.py')
    assert all(h['severity']=='CRITICAL' for h in hits)
    assert scan_local_console_detail_text_for_forbidden_markers('xtquant.xtdata xtdata','qmt_ai_trading/data.py') == []

def test_formatter_safety_note(tmp_path):
    _stage62(tmp_path); r=run_local_console_detail_review(LocalConsoleDetailConfig(repo_root=tmp_path))
    md=format_detail_report_md(r)
    assert '## Safety Note' in md
    assert 'READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW 只表示' in md

def test_cli_outputs(tmp_path):
    _stage62(tmp_path); out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_local_console_detail_review.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--output',str(out/'local_console_detail_report.md'),'--json-output',str(out/'local_console_detail_report.json'),'--filter-output',str(out/'filter_index.md'),'--filter-json-output',str(out/'filter_index.json'),'--warnings-output',str(out/'warnings.md'),'--warnings-json-output',str(out/'warnings.json'),'--blocking-output',str(out/'blocking_reasons.md'),'--blocking-json-output',str(out/'blocking_reasons.json'),'--manifest-output',str(out/'manifest_detail.md'),'--manifest-json-output',str(out/'manifest_detail.json'),'--validation-output',str(out/'validation_detail.md'),'--validation-json-output',str(out/'validation_detail.json'),'--plan-output',str(out/'next_console_overview_plan.md'),'--plan-json-output',str(out/'next_console_overview_plan.json')]
    assert subprocess.run(cmd,cwd=Path.cwd()).returncode == 0
    for f in ['local_console_detail_report.md','local_console_detail_report.json','filter_index.md','filter_index.json','warnings.md','warnings.json','blocking_reasons.md','blocking_reasons.json','manifest_detail.md','manifest_detail.json','validation_detail.md','validation_detail.json','next_console_overview_plan.md','next_console_overview_plan.json']:
        assert (out/f).exists()

def test_docs_and_validate_script_guards():
    gi=Path('.gitignore').read_text(encoding='utf-8')
    assert 'validation_logs/' in gi
    assert 'scripts/sync_all.ps1' not in subprocess.check_output(['git','diff','--name-only']).decode().splitlines()
    road=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    assert '完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）' in road
    assert 'Stage61-75' in road
    assert '不能绕过 Risk Gate / Human Approval' in road and '不能直接访问 QMT' in road and '不能自动 approve' in road
    ps=Path('scripts/validate_stage63.ps1').read_text(encoding='utf-8')
    assert 'powershell -NoProfile -Command' not in ps
    assert 'Clean-PythonCache' in ps
    assert ps.index('Clean-PythonCache') < ps.rindex('sync_all.ps1 -Mode scan')
