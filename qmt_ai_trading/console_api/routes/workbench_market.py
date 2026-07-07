from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from .common import CONSOLE, payload, read_json
from . import workbench_api_config


OPENAI_COMPAT_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'qmt-ai-trading-local-console/1.0 Market-Analysis',
}


def _artifact_path(module: str, name: str) -> str:
    return (CONSOLE / module / name).as_posix()


def _write_text(module: str, name: str, text: str) -> str:
    folder = CONSOLE / module
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(text, encoding='utf-8')
    return path.as_posix()


def _first_array(obj: Any) -> list[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for value in obj.values():
            arr = _first_array(value)
            if arr:
                return arr
    return []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ''):
            return default
        return float(value)
    except Exception:
        return default


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ''):
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _normalize_purposes(row: dict[str, Any]) -> list[str]:
    raw = row.get('purposes')
    return [str(x) for x in raw] if isinstance(raw, list) else []


def _priority(row: dict[str, Any]) -> int:
    try:
        return int(row.get('priority', 1))
    except Exception:
        return 1


def _market_rows() -> list[dict[str, Any]]:
    data = read_json('datahub', 'market_latest.json', {})
    return [row for row in _first_array(data) if isinstance(row, dict)]


def _symbols() -> list[str]:
    data = read_json('datahub', 'datahub_symbols.json', {'symbols': []})
    if isinstance(data, dict) and isinstance(data.get('symbols'), list):
        return [str(x) for x in data.get('symbols', [])]
    return []


def market_quotes():
    rows = []
    for idx, item in enumerate(_market_rows()):
        symbol = item.get('symbol') or item.get('code') or item.get('ts_code') or item.get('ticker') or f'ROW-{idx + 1}'
        latest = _num(item.get('latest') or item.get('price') or item.get('close') or item.get('lastPrice'))
        pre_close = _num(item.get('pre_close') or item.get('preClose') or item.get('last_close') or item.get('close'), latest)
        change = latest - pre_close if latest and pre_close else 0
        change_pct = round(change / pre_close * 100, 4) if pre_close else 0
        real_market_data = _bool(item.get('real_market_data'), False)
        sandbox_fallback = _bool(item.get('sandbox_fallback'), not real_market_data)
        rows.append({
            'id': str(symbol),
            'symbol': str(symbol),
            'name': item.get('name') or item.get('stock_name') or str(symbol),
            'time': item.get('time') or item.get('datetime') or item.get('updated_at') or '',
            'open': _num(item.get('open')),
            'high': _num(item.get('high')),
            'low': _num(item.get('low')),
            'close': _num(item.get('close'), latest),
            'latest': latest,
            'preClose': pre_close,
            'change': round(change, 4),
            'changePct': change_pct,
            'volume': _num(item.get('volume') or item.get('vol')),
            'amount': _num(item.get('amount') or item.get('turnover')),
            'status': 'NORMAL' if symbol else 'INVALID',
            'source': item.get('source') or 'datahub.market_latest',
            'realMarketData': real_market_data,
            'sandboxFallback': sandbox_fallback,
            'sourcePath': _artifact_path('datahub', 'market_latest.json'),
        })
    return payload(status='READY', source='datahub_market_latest', generated_at=datetime.now().isoformat(timespec='seconds'), data=rows)


def market_summary():
    quotes = market_quotes().get('data', [])
    symbols = _symbols()
    up = sum(1 for row in quotes if _num(row.get('changePct')) > 0)
    down = sum(1 for row in quotes if _num(row.get('changePct')) < 0)
    flat = max(0, len(quotes) - up - down)
    real_market_data = any(_bool(row.get('realMarketData'), False) for row in quotes)
    sandbox_fallback = bool(quotes) and not real_market_data and any(_bool(row.get('sandboxFallback'), True) for row in quotes)
    return payload(status='READY', source='datahub_market_latest', data={
        'quoteCount': len(quotes),
        'symbolCount': len(symbols),
        'upCount': up,
        'downCount': down,
        'flatCount': flat,
        'latestTime': max([str(row.get('time') or '') for row in quotes], default=''),
        'realMarketData': real_market_data,
        'sandboxFallback': sandbox_fallback,
        'dataMode': 'REAL_XTDATA' if real_market_data else ('SANDBOX_FALLBACK' if sandbox_fallback else 'UNKNOWN'),
        'sourcePath': _artifact_path('datahub', 'market_latest.json'),
    })


def _http_error_message(exc: urllib.error.HTTPError, url: str) -> str:
    try:
        body = exc.read(600).decode('utf-8', errors='replace')
    except Exception:
        body = ''
    return f'HTTP {exc.code}: {url}' + (f'；响应：{body[:360]}' if body else '')


def _call_openai_compatible(row: dict[str, Any], messages: list[dict[str, str]], max_tokens: int = 900) -> str:
    base_url = str(row.get('baseUrl') or '').rstrip('/')
    token = str(row.get('token') or '').strip()
    model = str(row.get('modelName') or '').strip()
    if not base_url or not token or not model:
        raise RuntimeError('AI 接口必须配置 Base URL、Token 和默认模型')
    body = {'model': model, 'messages': messages, 'max_tokens': max_tokens, 'temperature': 0.2, 'stream': False}
    req = urllib.request.Request(base_url + '/chat/completions', method='POST', data=json.dumps(body, ensure_ascii=False).encode('utf-8'))
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {token}')
    for key, value in OPENAI_COMPAT_HEADERS.items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:  # nosec - user configured local AI endpoint
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(_http_error_message(exc, base_url + '/chat/completions')) from exc
    choices = data.get('choices') if isinstance(data, dict) else None
    if not choices:
        raise RuntimeError('AI 接口返回为空：未发现 choices')
    message = choices[0].get('message') or {}
    content = message.get('content') or choices[0].get('text') or ''
    if not content:
        raise RuntimeError('AI 接口返回为空：未发现 content')
    return str(content).strip()


def _ai_config_candidates() -> list[dict[str, Any]]:
    try:
        rows = workbench_api_config._load()  # local private config store, token is only used server-side
    except Exception:
        rows = []
    candidates = []
    for row in rows:
        purposes = _normalize_purposes(row)
        if row.get('enabled') and ('ai' in purposes or 'research' in purposes or 'all' in purposes):
            candidates.append(row)
    return sorted(candidates, key=lambda x: (_priority(x), 0 if 'ai' in _normalize_purposes(x) or 'all' in _normalize_purposes(x) else 1, str(x.get('name') or '')))


def market_ai_analysis(body: dict[str, Any] | None = None):
    quotes = market_quotes().get('data', [])
    summary = market_summary().get('data', {})
    if not quotes:
        return payload(ok=False, status='FAILED', error='暂无行情数据，先运行“真实 xtdata 只读 smoke”或“只读行情快照”')
    candidates = _ai_config_candidates()
    if not candidates:
        return payload(ok=False, status='FAILED', error='未找到可用 AI 模型。请在 API 接口添加 AI 接口，并在配置中心分配“AI服务”或“全部”用途。')
    top_up = sorted(quotes, key=lambda x: _num(x.get('changePct')), reverse=True)[:8]
    top_down = sorted(quotes, key=lambda x: _num(x.get('changePct')))[:8]
    high_amount = sorted(quotes, key=lambda x: _num(x.get('amount')), reverse=True)[:8]
    context = {
        'summary': summary,
        'sample_size': len(quotes),
        'data_mode_note': 'SANDBOX_FALLBACK 表示当前不是实时真实行情，时间来自沙盒样例数据，仅用于链路测试。',
        'top_up': top_up,
        'top_down': top_down,
        'high_amount': high_amount,
    }
    prompt = (
        '你是A股量化交易系统的数据与行情分析助手。请基于以下行情快照输出一份中文分析报告。'
        '报告必须分为：1) 市场广度与方向；2) 涨跌结构；3) 成交额/流动性；4) 数据质量风险；'
        '5) 对因子研究和策略层的影响；6) 下一步建议。'
        '如果 dataMode=SANDBOX_FALLBACK，必须明确说明这不是实时行情，只能用于链路与页面功能验证。'
        '不要给出确定性买卖建议，不要生成真实下单指令，只做研究和风控视角分析。\n\n'
        f'行情数据：{json.dumps(context, ensure_ascii=False)[:9000]}'
    )
    errors = []
    selected = None
    report = ''
    for row in candidates:
        try:
            report = _call_openai_compatible(row, [
                {'role': 'system', 'content': '你是严谨的A股量化投研助手，只做研究分析，不输出下单指令。'},
                {'role': 'user', 'content': prompt},
            ])
            selected = row
            break
        except Exception as exc:
            errors.append(f'{row.get("name") or row.get("modelName")}: {exc}')
            continue
    if not selected:
        detail = '；'.join(errors[-5:])
        if 'HTTP 503' in detail:
            detail = '上游 AI 服务临时不可用（HTTP 503）。系统已尝试可用 AI 配置但仍失败，可稍后重试或切换模型。' + detail
        return payload(ok=False, status='FAILED', error=detail)
    generated_at = datetime.now().isoformat(timespec='seconds')
    artifact = _write_text('datahub', 'market_ai_analysis.md', f'# 行情数据 AI 分析\n\n生成时间：{generated_at}\n模型：{selected.get("modelName") or selected.get("name")}\n\n{report}\n')
    return payload(status='READY', source='market_ai_analysis', data={
        'status': 'READY',
        'modelName': selected.get('modelName') or selected.get('name') or '',
        'apiName': selected.get('name') or '',
        'generatedAt': generated_at,
        'report': report,
        'sourcePath': artifact,
    })
