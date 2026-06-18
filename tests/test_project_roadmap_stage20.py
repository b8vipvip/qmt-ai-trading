from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP = REPO_ROOT / "docs" / "qmt-ai-trading-project-roadmap.md"
STAGE20 = REPO_ROOT / "docs" / "stage20-roadmap-realignment.md"
ARCHITECTURE = REPO_ROOT / "docs" / "qmt-ai-trading-architecture.md"
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_all.ps1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_roadmap_exists() -> None:
    assert ROADMAP.exists()


def test_roadmap_contains_stage20_required_rules_and_boundaries() -> None:
    text = read(ROADMAP)
    assert "后续开发强制阅读规则" in text
    assert "AI 不直接下单" in text
    assert "QMT Gateway 是唯一真实交易边界" in text
    assert "阶段十九：Daily Pipeline 数据源切换策略" in text
    assert "Daily Pipeline 接入真实缓存行情" in text
    assert ("安全前置" in text) or ("工程化表达" in text)
    assert "阶段二十：项目路线总文档重审与阶段计划对齐" in text
    assert "阶段二十一：Human Approval 人工确认层" in text
    assert "每个阶段开发提示词必须写明当前阶段通过后的下一阶段计划" in text
    assert "不修改 `scripts/sync_all.ps1`" in text or "不修改 scripts/sync_all.ps1" in text


def test_stage20_realignment_doc_exists_and_explains_mismatch() -> None:
    assert STAGE20.exists()
    text = read(STAGE20)
    assert ("不是完全跑偏" in text) or ("工程拆分粒度不一致" in text)


def test_architecture_mentions_project_roadmap() -> None:
    text = read(ARCHITECTURE)
    assert "qmt-ai-trading-project-roadmap.md" in text


def test_sync_all_ps1_is_not_empty_or_replaced() -> None:
    text = read(SYNC_SCRIPT)
    assert SYNC_SCRIPT.exists()
    assert len(text) > 100
    assert "param" in text.lower()
