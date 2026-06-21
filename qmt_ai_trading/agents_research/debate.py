def build_debate(outputs):
    bull=next((o for o in outputs if o['agent_id']=='bull_agent'),{})
    bear=next((o for o in outputs if o['agent_id']=='bear_agent'),{})
    return {'dry_run':True,'not_live_trading':True,'research_only':True,'bull':bull,'bear':bear,'summary':'多空辩论仅用于研究对比，不构成交易指令。'}
