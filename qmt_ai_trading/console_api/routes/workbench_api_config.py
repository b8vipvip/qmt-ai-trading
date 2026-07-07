from __future__ import annotations

import json
import random
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .common import CONSOLE, payload

CONFIG_DIR = CONSOLE / 'system'
CONFIG_FILE = CONFIG_DIR / 'api_configs.private.json'
PROVIDERS = {'akshare', 'tushare', 'baostock', 'openai_compatible', 'custom_http'}
PURPOSES = {'market', 'fundamental', 'news', 'research', 'ai', 'all'}
PURPOSE_ORDER = ['market', 'fundamental', 'news', 'research', 'ai', 'all']


OPENAI_COMPAT_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'qmt-ai-trading-local-console/1.0 OpenAI-Compatible-Probe',
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any, max_len: int = 500) -> str:
    text = str(value or '').strip()
    return text[:max_len]


def _normalize_priority(value: Any) -> int:
    try:
        n = int(value)
    except Exception:
        n = 1
    return max(1, min(20, n))


def _normalize_purposes(row: dict[str, Any]) -> list[str]:
    raw = row.get('purposes')
    if isinstance(raw, list):
        values = [str(x) for x in raw if str(x) in PURPOSES]
    else:
        old = str(row.get('purpose') or '').strip()
        values = [old] if old in PURPOSES else []
    return sorted(set(values), key=lambda x: PURPOSE_ORDER.index(x))


def _default_purposes(provider: str) -> list[str]:
    if provider == 'openai_compatible':
        return sorted(set(['ai'] + random.choice([[], ['research']])), key=lambda x: PURPOSE_ORDER.index(x))
    return []


def _display_name(name: str, model: str, config_id: str) -> str:
    base = _clean_text(name or config_id, 120)
    model = _clean_text(model, 80)
    if model and model.lower() not in base.lower():
        return _clean_text(f'{base} · {model}', 160)
    return base


def _load() -> list[dict[str, Any]]:
    try:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
            if isinstance(data, dict) and isinstance(data.get('configs'), list):
                rows = [x for x in data['configs'] if isinstance(x, dict)]
                for row in rows:
                    row['purposes'] = _normalize_purposes(row)
                    row['priority'] = _normalize_priority(row.get('priority', 1))
                    row.pop('purpose', None)
                return rows
    except Exception:
        return []
    return []


def _save(rows: list[dict[str, Any]]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({'updated_at': _now(), 'configs': rows}, ensure_ascii=False, indent=2), encoding='utf-8')


def _mask(value: Any) -> str:
    text = str(value or '')
    if not text:
        return ''
    if len(text) <= 8:
        return '***'
    return text[:4] + '***' + text[-4:]


def _public(row: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in row.items() if k not in {'token', 'secret', 'password', 'xtdataPath'}}
    out['purposes'] = _normalize_purposes(row)
    out['priority'] = _normalize_priority(row.get('priority', 1))
    out['hasToken'] = bool(row.get('token'))
    out['tokenMasked'] = _mask(row.get('token'))
    out['sourcePath'] = CONFIG_FILE.as_posix()
    return out


def list_configs():
    rows = [x for x in _load() if x.get('provider') != 'qmt_xtdata']
    return payload(status='READY', source='local_api_config_store', data=[_public(x) for x in rows])


def save_config(body: dict[str, Any]):
    data = body.get('config') if isinstance(body.get('config'), dict) else body
    provider = _clean_text(data.get('provider'))
    if provider not in PROVIDERS:
        return payload(ok=False, status='FAILED', error='provider 不在白名单：akshare/tushare/baostock/openai_compatible/custom_http')
    rows = _load()
    config_id = _clean_text(data.get('id')) or f'{provider}-{len(rows) + 1}'
    existing = next((x for x in rows if x.get('id') == config_id), None)
    token = data.get('token')
    model_name = _clean_text(data.get('modelName'), 160)
    input_purposes = _normalize_purposes(data)
    purposes = _normalize_purposes(existing) if existing and not input_purposes else input_purposes
    if not purposes:
        purposes = _default_purposes(provider)
    row = {
        'id': config_id,
        'name': _display_name(_clean_text(data.get('name') or config_id, 120), model_name, config_id),
        'provider': provider,
        'baseUrl': _clean_text(data.get('baseUrl'), 300),
        'account': _clean_text(data.get('account'), 160),
        'modelName': model_name,
        'enabled': bool(data.get('enabled', True)),
        'note': _clean_text(data.get('note'), 500),
        'purposes': purposes,
        'priority': _normalize_priority(data.get('priority', (existing or {}).get('priority', 1))),
        'createdAt': (existing or {}).get('createdAt') or _now(),
        'updatedAt': _now(),
    }
    if token in (None, '') and existing:
        row['token'] = existing.get('token', '')
    else:
        row['token'] = _clean_text(token, 1000)
    rows = [x for x in rows if x.get('id') != config_id]
    rows.insert(0, row)
    _save(rows)
    return payload(status='SAVED', source='local_api_config_store', data=_public(row))


def set_purposes(body: dict[str, Any]):
    config_id = _clean_text(body.get('id'))
    purposes = body.get('purposes') or []
    if not isinstance(purposes, list):
        return payload(ok=False, status='FAILED', error='purposes 必须是数组')
    clean = [str(x) for x in purposes if str(x) in PURPOSES]
    if len(clean) != len(purposes):
        return payload(ok=False, status='FAILED', error='用途不在白名单：market/fundamental/news/research/ai/all')
    rows = _load()
    row = next((x for x in rows if x.get('id') == config_id and x.get('provider') != 'qmt_xtdata'), None)
    if not row:
        return payload(ok=False, status='FAILED', error='API 配置不存在')
    row['purposes'] = sorted(set(clean), key=lambda x: PURPOSE_ORDER.index(x))
    if 'priority' in body:
        row['priority'] = _normalize_priority(body.get('priority'))
    else:
        row['priority'] = _normalize_priority(row.get('priority', 1))
    row['updatedAt'] = _now()
    _save(rows)
    return payload(status='SAVED', source='local_api_config_store', data=_public(row))


def select_config_for_purpose(purpose: str) -> dict[str, Any] | None:
    purpose = _clean_text(purpose, 40)
    candidates = [x for x in _load() if x.get('enabled') and (purpose in _normalize_purposes(x) or 'all' in _normalize_purposes(x))]
    if not candidates:
        return None
    best_priority = min(_normalize_priority(x.get('priority', 1)) for x in candidates)
    best = [x for x in candidates if _normalize_priority(x.get('priority', 1)) == best_priority]
    return random.choice(best)


def _http_error_message(exc: urllib.error.HTTPError, url: str) -> str:
    try:
        body = exc.read(500).decode('utf-8', errors='replace')
    except Exception:
        body = ''
    detail = f'HTTP {exc.code}: {url}'
    if body:
        detail += f'；响应：{body[:260]}'
    if exc.code == 403 and ('1010' in body or 'error code: 1010' in body.lower()):
        detail += '；诊断：上游接口返回 Cloudflare/Error 1010，通常是中转站防火墙、IP、User-Agent 或接口权限限制，并不是前端页面错误。'
    return detail


def _request_json(url: str, token: str = '', method: str = 'GET', body: dict[str, Any] | None = None, extra_headers: dict[str, str] | None = None) -> tuple[str, str]:
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('Content-Type', 'application/json')
    for key, value in (extra_headers or {}).items():
        req.add_header(key, value)
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:  # nosec - user-configured local API probe
            raw = resp.read(240).decode('utf-8', errors='replace')
            msg = f'HTTP {resp.status}: {url}'
            if raw:
                msg += f'；响应：{raw[:180]}'
            return ('READY' if 200 <= resp.status < 400 else 'FAILED'), msg
    except urllib.error.HTTPError as exc:
        return 'FAILED', _http_error_message(exc, url)
    except Exception as exc:
        return 'FAILED', str(exc)


def _test_openai_compatible(row: dict[str, Any]) -> tuple[str, str]:
    base_url = _clean_text(row.get('baseUrl'), 300).rstrip('/')
    token = _clean_text(row.get('token'), 1000)
    model = _clean_text(row.get('modelName'), 160)
    if not base_url or not token:
        return 'FAILED', 'AI 接口必须配置 Base URL 和 Token'
    status, msg = _request_json(base_url + '/models', token=token, method='GET', extra_headers=OPENAI_COMPAT_HEADERS)
    if status == 'READY':
        return status, 'AI 接口 /models 测试通过：' + msg
    if model:
        body = {'model': model, 'messages': [{'role': 'user', 'content': 'ping'}], 'max_tokens': 1, 'stream': False}
        chat_status, chat_msg = _request_json(base_url + '/chat/completions', token=token, method='POST', body=body, extra_headers=OPENAI_COMPAT_HEADERS)
        if chat_status == 'READY':
            return chat_status, 'AI 接口 chat/completions 测试通过；/models 不可用但不影响调用。' + chat_msg
        if '1010' in (msg + chat_msg):
            return 'FAILED', f'上游 AI 接口被防火墙拒绝（Cloudflare/Error 1010）。请检查该中转站是否限制当前本机出口 IP、是否要求代理、是否禁止 Python/服务端请求，或更换 Base URL/节点。/models：{msg}；chat/completions：{chat_msg}'
        return 'FAILED', f'/models 测试失败：{msg}；chat/completions 测试失败：{chat_msg}'
    return 'FAILED', msg + '；部分中转站会禁用 /models，请填写默认模型后再测试 chat/completions。'


def test_config(body: dict[str, Any]):
    config_id = _clean_text(body.get('id'))
    row = next((x for x in _load() if x.get('id') == config_id and x.get('provider') != 'qmt_xtdata'), None)
    if not row:
        return payload(ok=False, status='FAILED', error='API 配置不存在')
    provider = row.get('provider')
    result = {'id': config_id, 'provider': provider, 'purposes': _normalize_purposes(row), 'priority': _normalize_priority(row.get('priority', 1)), 'enabled': row.get('enabled'), 'checkedAt': _now(), 'sourcePath': CONFIG_FILE.as_posix()}
    try:
        if provider == 'akshare':
            import akshare  # type: ignore
            result.update({'status': 'READY', 'message': f'AkShare 包可导入：{getattr(akshare, "__version__", "unknown")}'})
        elif provider == 'baostock':
            import baostock  # type: ignore
            result.update({'status': 'READY', 'message': f'BaoStock 包可导入：{getattr(baostock, "__version__", "unknown")}'})
        elif provider == 'tushare':
            import tushare  # type: ignore
            if not row.get('token'):
                result.update({'status': 'FAILED', 'message': 'Tushare 包可导入，但未配置 token'})
            else:
                result.update({'status': 'READY', 'message': f'Tushare 包可导入且 token 已保存：{getattr(tushare, "__version__", "unknown")}'})
        elif provider == 'openai_compatible':
            status, msg = _test_openai_compatible(row)
            result.update({'status': status, 'message': msg})
        elif provider == 'custom_http':
            if not row.get('baseUrl'):
                result.update({'status': 'FAILED', 'message': 'custom_http 必须配置 baseUrl'})
            else:
                status, msg = _request_json(str(row.get('baseUrl')).rstrip('/'), token=row.get('token') or '', method='GET')
                result.update({'status': status, 'message': msg})
        else:
            result.update({'status': 'FAILED', 'message': '未知 provider'})
    except Exception as exc:
        result.update({'status': 'FAILED', 'message': str(exc)})
    return payload(status=result['status'], source='local_api_config_test', data=result)
