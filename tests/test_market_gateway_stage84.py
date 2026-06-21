import json
from qmt_ai_trading.market_gateway import MockMarketDataProvider, SandboxMarketDataGateway, ReplayBus, run_market_gateway_stage84
from qmt_ai_trading.market_gateway.data_quality import build_quality_report

def test_mock_provider_gateway_replay_and_outputs(tmp_path):
    provider=MockMarketDataProvider(); symbols=provider.list_symbols(); assert symbols and symbols[0].sandbox and symbols[0].read_only
    gw=SandboxMarketDataGateway(provider); snaps=gw.get_snapshot(['510300.SH']); bars=gw.get_bars('510300.SH','1d',3)
    assert snaps[0].not_live_trading and snaps[0].no_qmt_trader_api and bars[0].sandbox
    events=ReplayBus(gw).replay(['510300.SH'],'1d',5)
    assert events and all(e['event_type'] in {'QUOTE','BAR','TICK','SNAPSHOT','HEARTBEAT'} for e in events)
    assert events == sorted(events, key=lambda e:(e['timestamp'], e['sequence']))
    quality=build_quality_report([s.to_dict() for s in symbols],[x.to_dict() for x in snaps],[x.to_dict() for x in bars])
    assert quality['data_quality'] in {'GOOD','WARNING','BAD'} and quality['sandbox'] and quality['not_live_trading']
    report=run_market_gateway_stage84('.', str(tmp_path/'out'))
    assert report['sandbox'] and report['read_only'] and report['no_qmt_trader_api']
    for name in ['market_input_context','market_symbols','market_snapshots','market_bars','replay_events','replay_session','market_data_quality','market_gateway_report','frontend_market_contract','next_qmt_xtdata_boundary_plan']:
        assert (tmp_path/'out'/f'{name}.json').exists()
        assert (tmp_path/'out'/f'{name}.md').exists()
