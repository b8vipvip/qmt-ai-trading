from pathlib import Path
import sys

roadmap = Path("docs/qmt-ai-trading-project-roadmap.md")
if not roadmap.exists():
    print(f"Missing roadmap file: {roadmap}")
    raise SystemExit(1)

text = roadmap.read_text(encoding="utf-8", errors="replace")

required = [
    "完整工程阶段计划与前端 UI 产品化路线",
    "Stage 1-75",
    "Stage61",
    "API Gateway",
    "Stage75",
    "本地控制台封版",
    "UI 不直接访问 QMT",
    "UI 不能绕过 Risk Gate",
    "UI 不能绕过 Human Approval",
    "UI 不能自动 approve",
]

missing = [item for item in required if item not in text]

if missing:
    print("Missing roadmap required text:")
    for item in missing:
        print(f"- {item}")
    raise SystemExit(1)

print("Roadmap Stage1-75 and UI productization plan check passed.")
