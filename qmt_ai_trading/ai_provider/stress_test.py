from __future__ import annotations
from .models import AiStressTestResult,AiModelBenchmarkReport,to_dict,AiProviderConfig
from .provider_client import ProviderClient
from .safety import assert_stress_test_limits,mask_api_key,assert_no_api_key_in_report
LATEST_BENCHMARK={}
PROMPT='你是 qmt-ai-trading 本地系统的模型连通性测试器。请阅读下面的测试文本，并用中文输出三项内容：1）摘要；2）结构化 JSON 字段；3）是否理解成功。不要给出投资建议，不要生成交易指令。'
def build_prompt(n): return PROMPT+'\n'+'本段为安全连通性测试文本。'*max(1,(n-len(PROMPT))//12)
def run_stress_test(provider_type,base_url,api_key,selected_models,test_sizes=None,timeout_seconds=90,endpoint_type='chat_completions'):
    models,sizes=assert_stress_test_limits(selected_models,test_sizes); c=ProviderClient(base_url,api_key,timeout_seconds); results=[]
    for m in models:
        for n in sizes:
            payload={'model':m,'messages':[{'role':'user','content':build_prompt(n)[:n]}],'temperature':0,'max_tokens':300}
            status,data,elapsed=c.request_json('POST',c.base_url+'/chat/completions',payload)
            text=str(data.get('choices',[{}])[0].get('message',{}).get('content','')) if isinstance(data,dict) else ''
            ok=200<=status<300
            results.append(AiStressTestResult(m,f'chars_{n}',n,ok,status,elapsed,len(text),None if ok else 'http_error',None if ok else str(data)[:240],data.get('usage',{}) if isinstance(data,dict) else {},'适合通用 Agent' if ok else '暂不推荐'))
    summary={'total':len(results),'success':sum(r.success for r in results),'failed':sum(not r.success for r in results),'max_concurrency':1,'score':round(100*sum(r.success for r in results)/max(1,len(results)),2)}
    rec={role:(models[0] if results and any(r.success for r in results) else '') for role in ['technical_agent','fundamental_agent','sentiment_agent','bull_bear_debate_agent','risk_agent','portfolio_manager_agent','fallback_model']}
    provider=to_dict(AiProviderConfig('session',provider_type,c.base_url,mask_api_key(api_key),timeout_seconds))
    report=AiModelBenchmarkReport(provider,models,results,summary,rec,['Stage78 仅测试摘要/格式化能力，不生成交易建议'])
    LATEST_BENCHMARK.clear(); LATEST_BENCHMARK.update(to_dict(report)); assert_no_api_key_in_report(LATEST_BENCHMARK,api_key); return report
