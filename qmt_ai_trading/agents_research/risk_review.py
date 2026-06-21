def build_risk_review(outputs, context):
    flags=[]
    for o in outputs: flags.extend(o.get('risk_flags',[]))
    flags.extend(context.get('warnings',[]))
    return {'dry_run':True,'not_live_trading':True,'research_only':True,'requires_risk_gate':True,'requires_human_approval':True,'risk_flags':sorted(set(flags)),'summary':'Risk Agent 保留上游 Risk Gate dry-run 阻断，不允许绕过风控。'}
