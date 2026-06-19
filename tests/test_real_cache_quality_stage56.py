from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.real_cache_quality.models import *
from qmt_ai_trading.real_cache_quality.service import *
from qmt_ai_trading.real_cache_quality.safety import scan_real_cache_quality_text_for_forbidden_markers
from qmt_ai_trading.real_cache_quality.cache_probe import probe_cache_roundtrip_with_mock_provider, probe_field_quality


def _stage55(root: Path, decision='READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW', critical=0):
    d=root/'qmt_dryrun_calibration_stage55'; d.mkdir()
    (d/'qmt_dryrun_calibration.json').write_text(json.dumps({'decision':decision,'summary':{'critical':critical},'blocking_reasons':[]}),encoding='utf-8')
    for n in ['qmt_dryrun_calibration.md','xtdata_capability.json','etf_whitelist_calibration.json','next_real_cache_quality_plan.json']:
        (d/n).write_text('{}',encoding='utf-8')

def _roadmap(root: Path):
    p=root/'docs'; p.mkdir()
    (p/'qmt-ai-trading-project-roadmap.md').write_text('完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）\nStage61：API Gateway 基础层\nStage75：本地控制台封版 / 可选桌面化\nUI 不直接访问 QMT\nUI 不能绕过 Risk Gate\nUI 不能绕过 Human Approval\nUI 不能自动 approve\n',encoding='utf-8')

def test_config_and_report_defaults():
    assert RealCacheQualityConfig().provider == 'mock'
    assert RealCacheQualityReport().decision == RealCacheQualityDecision.NEED_MORE_EVIDENCE

def test_missing_stage55_no_crash(tmp_path):
    _roadmap(tmp_path)
    r=run_real_cache_quality(build_default_real_cache_quality_config(repo_root=tmp_path))
    assert r.decision in {RealCacheQualityDecision.NEED_MORE_EVIDENCE, RealCacheQualityDecision.NO_GO}

def test_stage55_ready_can_continue(tmp_path):
    _roadmap(tmp_path); _stage55(tmp_path); probe_cache_roundtrip_with_mock_provider(tmp_path/'market_data_test_stage56')
    r=run_real_cache_quality(build_default_real_cache_quality_config(repo_root=tmp_path, min_days=1))
    assert r.decision in {RealCacheQualityDecision.READY_FOR_REAL_CACHE_QUALITY_REVIEW, RealCacheQualityDecision.NEED_MORE_EVIDENCE}

def test_stage55_nogo_or_critical_blocks(tmp_path):
    _roadmap(tmp_path); _stage55(tmp_path,'NO_GO',0)
    r=run_real_cache_quality(build_default_real_cache_quality_config(repo_root=tmp_path))
    assert r.decision == RealCacheQualityDecision.NO_GO
    (tmp_path/'qmt_dryrun_calibration_stage55'/'qmt_dryrun_calibration.json').write_text(json.dumps({'decision':'READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW','summary':{'critical':1}}),encoding='utf-8')
    assert run_real_cache_quality(build_default_real_cache_quality_config(repo_root=tmp_path)).decision == RealCacheQualityDecision.NO_GO

def test_cache_missing_and_roundtrip(tmp_path):
    _roadmap(tmp_path); _stage55(tmp_path)
    r=run_real_cache_quality(build_default_real_cache_quality_config(repo_root=tmp_path, cache_root='missing_cache'))
    assert any(e.status == RealCacheQualityStatus.UNAVAILABLE for e in r.evidence)
    assert any(e.status == RealCacheQualityStatus.PASS for e in [probe_cache_roundtrip_with_mock_provider(tmp_path/'market_data_test_stage56')])

def test_field_quality_issues(tmp_path):
    d=tmp_path/'market_data_test_stage56'/'510300.SH'/'1d'; d.mkdir(parents=True)
    f=d/'510300.SH.1d.bars.jsonl'
    f.write_text('\n'.join([
        json.dumps({'datetime':'2026-01-01','symbol':'510300.SH','open':1,'high':0.5,'low':2,'close':1,'volume':-1,'amount':-2}),
        json.dumps({'datetime':'2026-01-01','symbol':'510300.SH','open':1,'close':1}),
    ]),encoding='utf-8')
    items=probe_field_quality(tmp_path/'market_data_test_stage56')
    assert any(i.field=='duplicate_date' and i.issue_count>0 for i in items)
    assert any(i.field=='missing_ohlc' and i.issue_count>0 for i in items)
    assert any(i.field=='ohlc_logic' and i.issue_count>0 for i in items)
    assert any(i.field=='volume_amount' and i.issue_count>0 for i in items)

def test_safety_marker_classification():
    crit=scan_real_cache_quality_text_for_forbidden_markers('xttrader XtQuantTrader place_order query_stock_asset','runtime executable')
    assert all(s == RealCacheQualitySeverity.CRITICAL for _,s in crit)
    warn=scan_real_cache_quality_text_for_forbidden_markers('xttrader place_order marker definitions','docs/tests/safety marker definitions')
    assert all(s == RealCacheQualitySeverity.WARN for _,s in warn)
    assert not scan_real_cache_quality_text_for_forbidden_markers('xtquant.xtdata xtdata','runtime')

def test_formatter_and_cli_outputs(tmp_path):
    _roadmap(tmp_path); _stage55(tmp_path)
    out=tmp_path/'out'
    cmd=[sys.executable,'scripts/run_real_cache_quality.py','--repo-root',str(tmp_path),'--output-dir',str(out),'--cache-root','market_data_test_stage56','--output',str(out/'real_cache_quality.md'),'--json-output',str(out/'real_cache_quality.json'),'--gapfill-output',str(out/'long_sample_gap_fill.md'),'--gapfill-json-output',str(out/'long_sample_gap_fill.json'),'--field-output',str(out/'field_quality_review.md'),'--field-json-output',str(out/'field_quality_review.json'),'--plan-output',str(out/'next_backtest_attribution_plan.md'),'--plan-json-output',str(out/'next_backtest_attribution_plan.json')]
    res=subprocess.run(cmd,cwd=Path.cwd(),text=True,capture_output=True,timeout=30)
    assert res.returncode == 0, res.stderr
    text=(out/'real_cache_quality.md').read_text(encoding='utf-8')
    assert '## Safety Note' in text and '不是实盘授权' in text and 'READY_FOR_REAL_CACHE_QUALITY_REVIEW 只表示' in text
    for n in ['real_cache_quality.json','long_sample_gap_fill.md','long_sample_gap_fill.json','field_quality_review.md','field_quality_review.json','next_backtest_attribution_plan.md','next_backtest_attribution_plan.json']:
        assert (out/n).exists()

def test_repo_guards():
    assert Path('scripts/sync_all.ps1').exists()
    assert not list(Path('scripts').glob('validate_stage55.ps1.bak_stage55fix_*'))
    gi=Path('.gitignore').read_text(encoding='utf-8')
    assert 'validation_logs/' in gi
    road=Path('docs/qmt-ai-trading-project-roadmap.md').read_text(encoding='utf-8')
    for t in ['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']:
        assert t in road
