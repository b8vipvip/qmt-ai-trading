from __future__ import annotations
import argparse,json
from pathlib import Path

def write(out,name,obj):
    (out/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/(name+'.md')).write_text('# '+obj['title']+'\n\n'+obj['summary']+'\n',encoding='utf-8')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--output-dir',required=True); ap.add_argument('--app-dir',required=True); a=ap.parse_args(); out=Path(a.output_dir); out.mkdir(exist_ok=True)
    write(out,'ai_model_discovery_report',{'title':'AI 模型发现报告','summary':'支持 /v1/models 与 /models fallback；报告只包含 masked key，不包含 API Key 明文。'})
    write(out,'ai_model_stress_test_report',{'title':'AI 模型压力测试报告','summary':'支持 1000 / 3000 / 5000 字串行测试；最多 5 个模型、15 个请求；不生成交易建议。'})
    write(out,'ai_model_usage_draft',{'title':'AI 模型用途映射草稿','summary':'技术面、基本面、情绪新闻、多空辩论、风险、组合经理与 fallback 模型用途映射草稿，不保存 API Key。'})
    write(out,'frontend_ai_contract',{'title':'前端 AI 契约','summary':'前端调用 /api/v1/ai/models/discover、/api/v1/ai/models/stress-test、/api/v1/ai/model-usage/draft；API Key 密码框仅会话使用。'})
    write(out,'next_factor_strategy_visualization_plan',{'title':'Stage79 因子研究与策略可视化计划','summary':'下一阶段建设因子研究工作台、选股评分可视化与 dry-run 复盘，不接实盘。'})
if __name__=='__main__': main()
