from __future__ import annotations

import json
import re
import threading
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from .common import CONSOLE, payload, read_json
from . import workbench_api_config
from qmt_ai_trading.console_api.artifact_writer import write_task_output_to_console_artifacts


OPENAI_COMPAT_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'qmt-ai-trading-local-console/1.0 Market-Analysis',
}

AUTO_REFRESH_FILE = CONSOLE / 'market' / 'auto_refresh_settings.private.json'
UNIVERSE_FILE = CONSOLE / 'market' / 'universe_settings.private.json'
AUTO_REFRESH_LOCK = threading.Lock()
AUTO_REFRESH_THREAD: threading.Thread | None = None
AUTO_REFRESH_STOP = threading.Event()
AUTO_REFRESH_RUNTIME: dict[str, Any] = {
    'running': False,
    'lastRunAt': '',
    'lastStatus': 'IDLE',
    'lastMessage': '自动刷新未启动',
    'lastRealMarketData': False,
    'lastSandboxFallback': False,
    'lastFailureReason': '',
    'runCount': 0,
}

PRESET_UNIVERSES = {
    'broad_etf': {
        'name': '宽基ETF池',
        'description': '适合先做ETF轮动、低频验证和行情链路测试。',
        'symbols': ['510300.SH', '510500.SH', '512100.SH', '588000.SH', '159915.SZ', '510050.SH', '159919.SZ', '159922.SZ', '512880.SH', '512000.SH'],
    },
    'index_benchmark': {
        'name': '指数/基准池',
        'description': '用于基准、风格判断和策略对比。',
        'symbols': ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000905.SH', '000852.SH'],
    },
    'sector_etf': {
        'name': '行业/主题ETF池',
        'description': '用于行业轮动和板块热度跟踪。',
        'symbols': ['512800.SH', '512880.SH', '512000.SH', '512010.SH', '512660.SH', '515790.SH', '515030.SH', '159996.SZ', '516160.SH', '159928.SZ'],
    },
    'stock_core_sample': {
        'name': 'A股核心样例池',
        'description': '先用少量高流动性个股验证链路；全A同步后会替换为真实可交易池。',
        'symbols': ['600519.SH', '601318.SH', '600036.SH', '601166.SH', '600030.SH', '000333.SZ', '000651.SZ', '000858.SZ', '002415.SZ', '300750.SZ'],
    },
}

DEFAULT_UNIVERSE = {
    'preset': 'broad_etf',
    'name': PRESET_UNIVERSES['broad_etf']['name'],
    'symbols': PRESET_UNIVERSES['broad_etf']['symbols'],
    'customSymbolsText': '',
    'source': 'preset',
}

DEFAULT_AUTO_REFRESH = {
    'enabled': False,
    'intervalSec': 60,
    'period': '1d',
    'limit': 120,
    'onlyMissingCache': True,
}

_SYMBOL_RE = re.compile(r'^(\d{6})\.(SH|SZ|BJ)$', re.I)


def _artifact_path(module: str, name: str) -> str:
    return (CONSOLE / module / name).as_posix()


def _write_text(module: str, name: str, text: str) -> str:
    folder = CONSOLE / module
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(text, encoding='utf-8')
    return path.as_posix()


def _read_json_file(path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default
    return default


def _write_json_file(path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _normalize_symbol(value: Any) -> str:
    raw = str(value or '').strip().upper().replace(' ', '')
    if not raw:
        return ''
    raw = raw.replace('，', ',').replace('；', ',').replace(';', ',')
    if raw.startswith('SH') and len(raw) == 8:
        raw = raw[2:] + '.SH'
    elif raw.startswith('SZ') and len(raw) == 8:
        raw = raw[2:] + '.SZ'
    elif raw.startswith('BJ') and len(raw) == 8:
        raw = raw[2:] + '.BJ'
    elif raw.endswith('SH') and '.' not in raw and len(raw) == 8:
        raw = raw[:6] + '.SH'
    elif raw.endswith('SZ') and '.' not in raw and len(raw) == 8:
        raw = raw[:6] + '.SZ'
    elif raw.endswith('BJ') and '.' not in raw and len(raw) == 8:
        raw = raw[:6] + '.BJ'
    elif raw.isdigit() and len(raw) == 6:
        if raw.startswith(('5', '6', '9')):
            raw = raw + '.SH'
        elif raw.startswith(('0', '1', '2', '3')):
            raw = raw + '.SZ'
        elif raw.startswith(('4', '8')):
            raw = raw + '.BJ'
    return raw if _SYMBOL_RE.match(raw) else ''


def _split_symbols(value: Any) -> list[str]:
    if isinstance(value, list):
        raw_items = value
    else:
        text = str(value or '').replace('\n', ',').replace('\t', ',').replace('，', ',').replace('；', ',').replace(';', ',')
        raw_items = [x for x in text.split(',')]
    out: list[str] = []
    seen = set()
    for item in raw_items:
        symbol = _normalize_symbol(item)
        if symbol and symbol not in seen:
            seen.add(symbol)
            out.append(symbol)
    return out[:1000]


def _universe_presets() -> list[dict[str, Any]]:
    return [{'key': key, **value, 'symbolCount': len(value['symbols'])} for key, value in PRESET_UNIVERSES.items()]


def _universe_settings() -> dict[str, Any]:
    data = _read_json_file(UNIVERSE_FILE, {})
    if not isinstance(data, dict):
        data = {}
    preset = str(data.get('preset') or DEFAULT_UNIVERSE['preset'])
    if preset not in PRESET_UNIVERSES and preset != 'custom':
        preset = DEFAULT_UNIVERSE['preset']
    custom_text = str(data.get('customSymbolsText') or '')
    if preset == 'custom':
        symbols = _split_symbols(custom_text or data.get('symbols') or [])
        name = '自定义股票池'
        source = 'custom'
    else:
        symbols = _split_symbols(data.get('symbols') or PRESET_UNIVERSES[preset]['symbols'])
        name = PRESET_UNIVERSES[preset]['name']
        source = 'preset'
    if not symbols:
        symbols = list(DEFAULT_UNIVERSE['symbols'])
        preset = DEFAULT_UNIVERSE['preset']
        name = DEFAULT_UNIVERSE['name']
        source = 'preset'
    return {
        'preset': preset,
        'name': name,
        'symbols': symbols,
        'symbolCount': len(symbols),
        'customSymbolsText': custom_text,
        'source': source,
        'presets': _universe_presets(),
        'sourcePath': UNIVERSE_FILE.as_posix(),
    }


def _auto_settings() -> dict[str, Any]:
    data = _read_json_file(AUTO_REFRESH_FILE, {})
    if not isinstance(data, dict):
        data = {}
    out = {**DEFAULT_AUTO_REFRESH, **data}
    try:
        out['intervalSec'] = max(10, min(3600, int(out.get('intervalSec') or 60)))
    except Exception:
        out['intervalSec'] = 60
    try:
        out['limit'] = max(1, min(500, int(out.get('limit') or 120)))
    except Exception:
        out['limit'] = 120
    universe = _universe_settings()
    symbols = _split_symbols(out.get('symbols') or universe.get('symbols') or DEFAULT_UNIVERSE['symbols'])
    if not symbols:
        symbols = list(DEFAULT_UNIVERSE['symbols'])
    out['symbols'] = symbols[:1000]
    out['universeName'] = universe.get('name')
    out['universePreset'] = universe.get('preset')
    out['universeSymbolCount'] = len(out['symbols'])
    out['period'] = str(out.get('period') or '1d')[:20]
    out['onlyMissingCache'] = bool(out.get('onlyMissingCache', True))
    out['enabled'] = bool(out.get('enabled', False))
    return out


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


def _cached_symbol_set() -> set[str]:
    return {str(row.get('symbol')) for row in _market_rows() if row.get('symbol')}


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
    universe = _universe_settings()
    up = sum(1 for row in quotes if _num(row.get('changePct')) > 0)
    down = sum(1 for row in quotes if _num(row.get('changePct')) < 0)
    flat = max(0, len(quotes) - up - down)
    real_market_data = any(_bool(row.get('realMarketData'), False) for row in quotes)
    sandbox_fallback = bool(quotes) and not real_market_data and any(_bool(row.get('sandboxFallback'), True) for row in quotes)
    return payload(status='READY', source='datahub_market_latest', data={
        'quoteCount': len(quotes),
        'symbolCount': len(symbols),
        'universeName': universe.get('name'),
        'universeSymbolCount': universe.get('symbolCount'),
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


def _auto_refresh_once(settings: dict[str, Any]) -> dict[str, Any]:
    from qmt_ai_trading.market_gateway import run_xtdata_live_stage87
    with AUTO_REFRESH_LOCK:
        AUTO_REFRESH_RUNTIME['running'] = True
        AUTO_REFRESH_RUNTIME['lastStatus'] = 'CHECKING_QMT'
        AUTO_REFRESH_RUNTIME['lastMessage'] = '正在检查 QMT 客户端和 xtdata 登录状态'
    try:
        try:
            from . import workbench_system
            qmt_check = workbench_system.test_qmt_settings({'kind': 'qmtClientPath'}).get('data', {})
        except Exception as exc:
            qmt_check = {'status': 'FAILED', 'message': f'QMT 客户端检查失败：{exc}'}
        symbols = list(settings.get('symbols') or DEFAULT_UNIVERSE['symbols'])
        requested_count = len(symbols)
        if settings.get('onlyMissingCache'):
            cached = _cached_symbol_set()
            missing = [s for s in symbols if s not in cached]
            if missing:
                symbols = missing
            elif cached:
                AUTO_REFRESH_RUNTIME.update({'lastStatus': 'CACHE_HIT', 'lastMessage': f'Universe 本地已有缓存，本轮未重复下载。当前 Universe：{settings.get("universeName")}，标的数：{requested_count}', 'lastRunAt': datetime.now().isoformat(timespec='seconds'), 'running': False})
                return dict(AUTO_REFRESH_RUNTIME)
        report = run_xtdata_live_stage87(
            repo_root='.',
            output_dir='local_console_xtdata_live_stage87',
            enabled=True,
            allow_import_xtdata=True,
            allow_real_market_data=True,
            allow_connect_miniqmt=True,
            read_only=True,
            allow_xttrader=False,
            allow_account_query=False,
            allow_order_submit=False,
            symbols=symbols,
            period=str(settings.get('period') or '1d'),
            limit=int(settings.get('limit') or 120),
        )
        write_task_output_to_console_artifacts('xtdata_live_readonly_smoke', report)
        message = report.get('failure_reason') or ('已获取并缓存真实行情' if report.get('real_market_data') else '未获取真实行情，已回退沙盒样例')
        AUTO_REFRESH_RUNTIME.update({
            'lastRunAt': datetime.now().isoformat(timespec='seconds'),
            'lastStatus': 'REAL_MARKET_DATA' if report.get('real_market_data') else 'WAITING_LOGIN_OR_FALLBACK',
            'lastMessage': f"Universe：{settings.get('universeName')}；请求标的 {requested_count} 个，本轮下载 {len(symbols)} 个；{qmt_check.get('message', '')}；{message}" if qmt_check else message,
            'lastRealMarketData': bool(report.get('real_market_data')),
            'lastSandboxFallback': bool(report.get('sandbox_fallback')),
            'lastFailureReason': str(report.get('failure_reason') or ''),
            'runCount': int(AUTO_REFRESH_RUNTIME.get('runCount') or 0) + 1,
            'running': False,
        })
        return dict(AUTO_REFRESH_RUNTIME)
    except Exception as exc:
        AUTO_REFRESH_RUNTIME.update({'lastRunAt': datetime.now().isoformat(timespec='seconds'), 'lastStatus': 'FAILED', 'lastMessage': str(exc), 'lastFailureReason': str(exc), 'running': False})
        return dict(AUTO_REFRESH_RUNTIME)


def _auto_loop() -> None:
    while not AUTO_REFRESH_STOP.is_set():
        settings = _auto_settings()
        if not settings.get('enabled'):
            break
        _auto_refresh_once(settings)
        AUTO_REFRESH_STOP.wait(max(10, int(settings.get('intervalSec') or 60)))
    with AUTO_REFRESH_LOCK:
        AUTO_REFRESH_RUNTIME['running'] = False


def _ensure_auto_thread() -> None:
    global AUTO_REFRESH_THREAD
    settings = _auto_settings()
    if not settings.get('enabled'):
        AUTO_REFRESH_STOP.set()
        return
    if AUTO_REFRESH_THREAD and AUTO_REFRESH_THREAD.is_alive():
        return
    AUTO_REFRESH_STOP.clear()
    AUTO_REFRESH_THREAD = threading.Thread(target=_auto_loop, name='qmt-market-auto-refresh', daemon=True)
    AUTO_REFRESH_THREAD.start()


def market_universe_status():
    universe = _universe_settings()
    return payload(status='READY', source='market_universe', data=universe)


def save_market_universe(body: dict[str, Any] | None = None):
    body = body or {}
    preset = str(body.get('preset') or DEFAULT_UNIVERSE['preset'])
    custom_text = str(body.get('customSymbolsText') or '')
    if preset not in PRESET_UNIVERSES and preset != 'custom':
        return payload(ok=False, status='FAILED', error='未知 Universe 类型')
    if preset == 'custom':
        symbols = _split_symbols(custom_text)
        if not symbols:
            return payload(ok=False, status='FAILED', error='自定义 Universe 至少需要 1 个合法证券代码，例如 510300.SH')
        data = {'preset': 'custom', 'name': '自定义股票池', 'symbols': symbols, 'customSymbolsText': '\n'.join(symbols), 'source': 'custom'}
    else:
        preset_symbols = PRESET_UNIVERSES[preset]['symbols']
        data = {'preset': preset, 'name': PRESET_UNIVERSES[preset]['name'], 'symbols': preset_symbols, 'customSymbolsText': custom_text, 'source': 'preset'}
    _write_json_file(UNIVERSE_FILE, data)
    AUTO_REFRESH_RUNTIME.update({'lastStatus': 'UNIVERSE_UPDATED', 'lastMessage': f'行情 Universe 已更新：{data["name"]}，标的数 {len(data["symbols"])}。自动刷新将按新 Universe 获取缺失缓存。'})
    return market_universe_status()


def market_auto_refresh_status():
    _ensure_auto_thread()
    settings = _auto_settings()
    runtime = dict(AUTO_REFRESH_RUNTIME)
    runtime['threadAlive'] = bool(AUTO_REFRESH_THREAD and AUTO_REFRESH_THREAD.is_alive())
    return payload(status='READY', source='market_auto_refresh', data={**settings, **runtime, 'sourcePath': AUTO_REFRESH_FILE.as_posix()})


def save_market_auto_refresh(body: dict[str, Any] | None = None):
    body = body or {}
    current = _auto_settings()
    next_settings = {**current}
    if 'enabled' in body:
        next_settings['enabled'] = bool(body.get('enabled'))
    if 'intervalSec' in body:
        try:
            next_settings['intervalSec'] = max(10, min(3600, int(body.get('intervalSec') or 60)))
        except Exception:
            next_settings['intervalSec'] = 60
    if 'onlyMissingCache' in body:
        next_settings['onlyMissingCache'] = bool(body.get('onlyMissingCache'))
    # Universe is configured separately and should not be duplicated into auto-refresh settings.
    next_settings.pop('symbols', None)
    next_settings.pop('universeName', None)
    next_settings.pop('universePreset', None)
    next_settings.pop('universeSymbolCount', None)
    _write_json_file(AUTO_REFRESH_FILE, next_settings)
    if next_settings.get('enabled'):
        AUTO_REFRESH_STOP.clear()
        _ensure_auto_thread()
        AUTO_REFRESH_RUNTIME.update({'lastStatus': 'AUTO_REFRESH_ENABLED', 'lastMessage': '自动刷新已启用，后台将按当前 Universe 检查 QMT 连接并刷新缺失行情缓存。'})
    else:
        AUTO_REFRESH_STOP.set()
        AUTO_REFRESH_RUNTIME.update({'lastStatus': 'AUTO_REFRESH_DISABLED', 'lastMessage': '自动刷新已关闭。', 'running': False})
    return market_auto_refresh_status()


def market_ai_analysis(body: dict[str, Any] | None = None):
    quotes = market_quotes().get('data', [])
    summary = market_summary().get('data', {})
    if not quotes:
        return payload(ok=False, status='FAILED', error='暂无行情数据，请先开启自动刷新行情并等待 QMT / xtdata 获取缓存')
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
        '报告必须分为：1) 当前 Universe 覆盖范围；2) 市场广度与方向；3) 涨跌结构；4) 成交额/流动性；5) 数据质量风险；'
        '6) 对因子研究和策略层的影响；7) 下一步建议。'
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
