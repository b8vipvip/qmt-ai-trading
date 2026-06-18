import json, subprocess, sys
from pathlib import Path
import pytest
from qmt_ai_trading.agent.models import AgentActionPolicy, AgentResearchContext, AgentResearchMemo
from qmt_ai_trading.agent.safety import assert_agent_read_only, sanitize_agent_context, validate_agent_memo_safety
from qmt_ai_trading.agent.summarizer import AgentSummarizerConfig, summarize_with_local_rules, build_candidate_comparison, build_human_review_checklist
from qmt_ai_trading.agent.formatters import format_agent_research_memo_markdown

ROOT = Path(__file__).resolve().parents[1]

def test_models_and_policy_defaults():
    ctx=AgentResearchContext(run_id="r1"); memo=AgentResearchMemo(run_id="r1"); pol=AgentActionPolicy()
    assert ctx.run_id == memo.run_id == "r1"
    assert not any(getattr(pol, n) for n in vars(pol) if n.startswith("allow_"))
    assert_agent_read_only(pol)
    with pytest.raises(ValueError): assert_agent_read_only(AgentActionPolicy(allow_qmt_access=True))

def test_sanitize_no_sensitive_values():
    ctx=AgentResearchContext(metadata={"token":"abc", "nested":{"password":"pw", "safe":"ok"}})
    text=json.dumps(sanitize_agent_context(ctx).metadata)
    assert "abc" not in text and "pw" not in text and "<redacted>" in text

def test_local_rules_deterministic_candidate_checklist_and_safety():
    ctx=AgentResearchContext(run_id="r", candidates=[{"symbol":"510300.SH","score":2,"eligible":True,"reason":"factor"}], risk_decisions=[{"allowed": True}])
    cfg=AgentSummarizerConfig()
    m1=summarize_with_local_rules(ctx,cfg); m2=summarize_with_local_rules(ctx,cfg)
    assert m1.executive_summary == m2.executive_summary
    assert "510300.SH" in build_candidate_comparison(ctx)
    checklist="\n".join(build_human_review_checklist(ctx))
    assert "Risk Gate" in checklist and "Human Approval" in checklist and "Paper Trading" in checklist
    bad=AgentResearchMemo(executive_summary="立即下单")
    assert validate_agent_memo_safety(bad)["blocked"]
    assert "Agent Research is read-only" in format_agent_research_memo_markdown(m1)

def test_run_agent_research_cli_no_inputs(tmp_path):
    md=tmp_path/"agent.md"; js=tmp_path/"agent.json"
    r=subprocess.run([sys.executable,"scripts/run_agent_research.py","--output",str(md),"--json-output",str(js),"--mode","local_rules","--include-monitoring","--include-backtest","--include-human-checklist"], cwd=ROOT, text=True, capture_output=True)
    assert r.returncode == 0, r.stderr + r.stdout
    assert md.exists() and js.exists()
    assert "Safety note" in md.read_text(encoding="utf-8")

def test_run_agent_research_external_disabled(tmp_path):
    md=tmp_path/"agent.md"
    r=subprocess.run([sys.executable,"scripts/run_agent_research.py","--output",str(md),"--mode","external_llm_disabled"], cwd=ROOT, text=True, capture_output=True)
    assert r.returncode == 0
    assert "External LLM mode is disabled" in md.read_text(encoding="utf-8")

def test_daily_and_scheduled_and_register_agent_research(tmp_path):
    out=tmp_path/"agent_reports"
    args=[sys.executable,"scripts/run_daily_pipeline.py","--data-source-mode","mock","--enable-agent-research","--agent-research-output-dir",str(out),"--agent-research-mode","local_rules"]
    r=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
    assert r.returncode == 0, r.stderr + r.stdout
    assert "## Agent Research" in r.stdout
    r2=subprocess.run([sys.executable,"scripts/run_scheduled_daily_pipeline.py","--data-source-mode","mock","--enable-agent-research","--agent-research-output-dir",str(out)],cwd=ROOT,text=True,capture_output=True)
    assert r2.returncode == 0, r2.stderr + r2.stdout
    r3=subprocess.run([sys.executable,"scripts/register_daily_pipeline_task.py","--enable-agent-research","--agent-research-output-dir","agent_reports","--agent-research-mode","local_rules"],cwd=ROOT,text=True,capture_output=True)
    assert r3.returncode == 0
    assert "--enable-agent-research" in r3.stdout and "--agent-research-mode local_rules" in r3.stdout

def test_docs_gitignore_and_sync_script_untouched():
    gi=(ROOT/".gitignore").read_text(encoding="utf-8")
    assert "agent_reports/" in gi or "agent_reports_stage29/" in gi
    roadmap=(ROOT/"docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段二十九" in roadmap and "Agent Research Layer" in roadmap
    assert "阶段三十" in roadmap and "小资金实盘灰度准备" in roadmap
    assert (ROOT/"scripts/sync_all.ps1").exists()
