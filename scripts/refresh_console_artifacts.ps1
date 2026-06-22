param([string]$Root='.')
$ErrorActionPreference='Stop'
$base=Join-Path $Root 'artifacts/reports/console'
$mods='workflow','market','datahub','research','strategy','risk','agent','backtest','paper','monitoring','approval','account_readonly','safety'
foreach($m in $mods){New-Item -ItemType Directory -Force -Path (Join-Path $base $m)|Out-Null}
$safety=@{read_only=$true;dry_run=$true;live_disabled=$true;no_order_submitted=$true;requires_human_approval=$true;account_masked=$true;order_submit_enabled=$false;order_cancel_enabled=$false;real_order_submitted=$false;updated_at=(Get-Date).ToString('s')}
function W($m,$n,$o){$p=Join-Path (Join-Path $base $m) $n; ($safety+$o)|ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $p}
W workflow 'workflow_status.json' @{status='EMPTY'; modules=$mods}
W workflow 'feature_matrix.json' @{status='EMPTY'; features=$mods}
W market 'xtdata_live_status.json' @{status='DISABLED_FOR_SAFETY'; real_market_data=$false; no_xttrader=$true}
W datahub 'datahub_status.json' @{status='EMPTY'; cache_status='DATA_MISSING'}; W datahub 'datahub_symbols.json' @{symbols=@()}; W datahub 'datahub_real_cache.json' @{status='DATA_MISSING'}; W datahub 'market_latest.json' @{status='DATA_MISSING'}
W research 'factor_context.json' @{status='EMPTY'}; W research 'factor_values.json' @{factors=@()}; W research 'factor_candidates.json' @{candidates=@()}
W strategy 'strategy_signals.json' @{signals=@()}; W strategy 'trade_intents.json' @{trade_intents=@()}
W risk 'risk_decisions.json' @{decisions=@()}; W risk 'risk_report.json' @{status='EMPTY'}
W agent 'agent_context.json' @{status='EMPTY'}; W agent 'agent_research_report.json' @{status='EMPTY'}
W backtest 'shadow_replay_result.json' @{status='EMPTY'}
W paper 'paper_trading_report.json' @{status='EMPTY'}; W paper 'paper_orders.json' @{orders=@()}; W paper 'shadow_positions.json' @{positions=@()}; W paper 'shadow_pnl.json' @{pnl=@{}}
W monitoring 'monitoring_input_context.json' @{status='EMPTY'}; W monitoring 'monitoring_alerts.json' @{alerts=@()}; W monitoring 'circuit_breaker_status.json' @{status='DISABLED_FOR_SAFETY'}
W approval 'approval_requests.json' @{requests=@(); approval_enabled=$false}
W account_readonly 'account_readonly_report.json' @{status='DISABLED_FOR_SAFETY'; account_id='***MASKED***'}
W safety 'safety_status.json' @{status='DISABLED_FOR_SAFETY'}
$idx=@{updated_at=(Get-Date).ToString('s'); modules=@{}}
foreach($m in $mods){$idx.modules[$m]=@{path="artifacts/reports/console/$m"; status='READY_EMPTY'}}
$idx|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 (Join-Path $base 'index.json')
Write-Host "refreshed $base"
