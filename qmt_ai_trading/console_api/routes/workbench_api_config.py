from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import CONSOLE, payload

CONFIG_DIR = CONSOLE / 'system'
CONFIG_FILE = CONFIG_DIR / 'api_configs.private.json'
PROVIDERS = {'akshare', 'tushare', 'baostock', 'qmt_xtdata', 'openai_compatible', 'custom_http'}
PURPOSES = {'market', 'fundamental', 'news', 'research', 'ai', 'all'}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any, max_len: int = 500) -> str:
    text = str(value or '').strip()
    return text[:max_len]


def _normalize_purposes(row: dict[str, Any]) -> list[str]:
    raw = row.get('purposes')
    if isinstance(raw, list):
        values = [str(x) for x in raw if str(x) in PURPOSES]
    else:
        old = str(row.get('purpose') or '').strip()
        values = [old] if old in PURPOSES else []
    return sorted(set(values), key=lambda x: ['market', 'fundamental', 'news', 'research', 'ai', 'all'].index(x))


def _load() -> list[dict[str, Any]]:
    try:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
            if isinstance(data, dict) and isinstance(data.get('configs'), list):
                rows = [x for x in data['configs'] if isinstance(x, dict)]
                for row in rows:
                    row['purposes'] = _normalize_purposes(row)
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
    out = {k: v for k, v in row.items() if k not in {'token', 'secret', 'password'}}
    out['purposes'] = _normalize_purposes(row)
    out['hasToken'] = bool(row.get('token'))
    out['tokenMasked'] = _mask(row.get('token'))
    out['sourcePath'] = CONFIG_FILE.as_posix()
    return out


def list_configs():
    return payload(status='READY', source='local_api_config_store', data=[_public(x) for x in _load()])


def save_config(body: dict[str, Any]):
    data = body.get('config') if isinstance(body.get('config'), dict) else body
    provider = _clean_text(data.get('provider'))
    if provider not in PROVIDERS:
        return payload(ok=False, status='FAILED', error='provider 不在白名单：akshare/tushare/baostock/qmt_xtdata/openai_compatible/custom_http')
    rows = _load()
    config_id = _clean_text(data.get('id')) or f'{provider}-{len(rows) + 1}'
    existing = next((x for x in rows if x.get('id') == config_id), None)
    token = data.get('token')
    row = {
        'id': config_id,
        'name': _clean_text(data.get('name') or config_id, 120),
        'provider': provider,
        'baseUrl': _clean_text(data.get('baseUrl'), 300),
        'account': _clean_text(data.get('account'), 160),
        'xtdataPath': _clean_text(data.get('xtdataPath'), 500),
        'modelName': _clean_text(data.get('modelName'), 160),
        'enabled': bool(data.get('enabled', True)),
        'note': _clean_text(data.get('note'), 500),
        'purposes': _normalize_purposes(existing or data),
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
    row = next((x for x in rows if x.get('id') == config_id), None)
    if not row:
        return payload(ok=False, status='FAILED', error='API 配置不存在')
    row['purposes'] = sorted(set(clean), key=lambda x: ['market', 'fundamental', 'news', 'research', 'ai', 'all'].index(x))
    row['updatedAt'] = _now()
    _save(rows)
    return payload(status='SAVED', source='local_api_config_store', data=_public(row))


def _http_probe(base_url: str, token: str = '', models_endpoint: bool = False) -> tuple[str, str]:
    url = base_url.rstrip('/')
    if models_endpoint:
        url = url + '/models'
    req = urllib.request.Request(url, method='GET')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=8) as resp:  # nosec - user-configured local data/API endpoint probe
        return 'READY' if 200 <= resp.status < 400 else 'FAILED', f'HTTP {resp.status}: {url}'


def test_config(body: dict[str, Any]):
    config_id = _clean_text(body.get('id'))
    row = next((x for x in _load() if x.get('id') == config_id), None)
    if not row:
        return payload(ok=False, status='FAILED', error='API 配置不存在')
    provider = row.get('provider')
    result = {'id': config_id, 'provider': provider, 'purposes': _normalize_purposes(row), 'enabled': row.get('enabled'), 'checkedAt': _now(), 'sourcePath': CONFIG_FILE.as_posix()}
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
        elif provider == 'qmt_xtdata':
            xt_path = row.get('xtdataPath') or ''
            path_msg = ''
            if xt_path:
                path_msg = '；路径存在' if Path(xt_path).exists() else '；路径不存在，请检查 QMT/xtdata 路径'
            try:
                from xtquant import xtdata  # type: ignore
                result.update({'status': 'READY', 'message': 'xtquant.xtdata 可导入' + path_msg})
            except Exception as exc:
                result.update({'status': 'FAILED', 'message': f'xtquant.xtdata 不可导入：{exc}{path_msg}'})
        elif provider == 'openai_compatible':
            if not row.get('baseUrl') or not row.get('token'):
                result.update({'status': 'FAILED', 'message': 'AI 接口必须配置 Base URL 和 Token'})
            else:
                status, msg = _http_probe(row.get('baseUrl'), row.get('token'), models_endpoint=True)
                result.update({'status': status, 'message': msg})
        elif provider == 'custom_http':
            if not row.get('baseUrl'):
                result.update({'status': 'FAILED', 'message': 'custom_http 必须配置 baseUrl'})
            else:
                status, msg = _http_probe(row.get('baseUrl'), row.get('token'), models_endpoint=False)
                result.update({'status': status, 'message': msg})
        else:
            result.update({'status': 'FAILED', 'message': '未知 provider'})
    except Exception as exc:
        result.update({'status': 'FAILED', 'message': str(exc)})
    return payload(status=result['status'], source='local_api_config_test', data=result)
