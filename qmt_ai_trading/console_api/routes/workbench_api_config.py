from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import CONSOLE, payload

CONFIG_DIR = CONSOLE / 'system'
CONFIG_FILE = CONFIG_DIR / 'api_configs.private.json'
PROVIDERS = {'akshare', 'tushare', 'baostock', 'qmt_xtdata', 'custom_http'}
PURPOSES = {'market', 'fundamental', 'news', 'research', 'all'}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load() -> list[dict[str, Any]]:
    try:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
            if isinstance(data, dict) and isinstance(data.get('configs'), list):
                return [x for x in data['configs'] if isinstance(x, dict)]
    except Exception:
        return []
    return []


def _save(rows: list[dict[str, Any]]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({'updated_at': _now(), 'configs': rows}, ensure_ascii=False, indent=2), encoding='utf-8')


def _clean_text(value: Any, max_len: int = 500) -> str:
    text = str(value or '').strip()
    return text[:max_len]


def _mask(value: Any) -> str:
    text = str(value or '')
    if not text:
        return ''
    if len(text) <= 8:
        return '***'
    return text[:4] + '***' + text[-4:]


def _public(row: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in row.items() if k not in {'token', 'secret', 'password'}}
    out['hasToken'] = bool(row.get('token'))
    out['tokenMasked'] = _mask(row.get('token'))
    out['sourcePath'] = CONFIG_FILE.as_posix()
    return out


def list_configs():
    return payload(status='READY', source='local_api_config_store', data=[_public(x) for x in _load()])


def save_config(body: dict[str, Any]):
    data = body.get('config') if isinstance(body.get('config'), dict) else body
    provider = _clean_text(data.get('provider'))
    purpose = _clean_text(data.get('purpose') or 'all')
    if provider not in PROVIDERS:
        return payload(ok=False, status='FAILED', error='provider 不在白名单：akshare/tushare/baostock/qmt_xtdata/custom_http')
    if purpose not in PURPOSES:
        return payload(ok=False, status='FAILED', error='purpose 不在白名单：market/fundamental/news/research/all')
    rows = _load()
    config_id = _clean_text(data.get('id')) or f'{provider}-{purpose}'
    existing = next((x for x in rows if x.get('id') == config_id), None)
    token = data.get('token')
    row = {
        'id': config_id,
        'name': _clean_text(data.get('name') or config_id, 120),
        'provider': provider,
        'purpose': purpose,
        'baseUrl': _clean_text(data.get('baseUrl'), 300),
        'account': _clean_text(data.get('account'), 160),
        'enabled': bool(data.get('enabled', True)),
        'note': _clean_text(data.get('note'), 500),
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


def test_config(body: dict[str, Any]):
    config_id = _clean_text(body.get('id'))
    row = next((x for x in _load() if x.get('id') == config_id), None)
    if not row:
        return payload(ok=False, status='FAILED', error='API 配置不存在')
    provider = row.get('provider')
    result = {'id': config_id, 'provider': provider, 'purpose': row.get('purpose'), 'enabled': row.get('enabled'), 'checkedAt': _now(), 'sourcePath': CONFIG_FILE.as_posix()}
    try:
        if provider == 'akshare':
            import akshare  # type: ignore
            result.update({'status': 'READY', 'message': f'AkShare 可导入：{getattr(akshare, "__version__", "unknown")}'})
        elif provider == 'baostock':
            import baostock  # type: ignore
            result.update({'status': 'READY', 'message': 'BaoStock 包可导入；登录/查询将在数据任务中执行'})
        elif provider == 'tushare':
            import tushare  # type: ignore
            if not row.get('token'):
                result.update({'status': 'FAILED', 'message': 'Tushare 包可导入，但未配置 token'})
            else:
                result.update({'status': 'READY', 'message': f'Tushare 可导入且 token 已配置：{getattr(tushare, "__version__", "unknown")}'})
        elif provider == 'qmt_xtdata':
            try:
                from xtquant import xtdata  # type: ignore
                result.update({'status': 'READY', 'message': 'xtquant.xtdata 可导入；行情读取请在数据中心执行只读任务'})
            except Exception as exc:
                result.update({'status': 'FAILED', 'message': f'xtquant.xtdata 不可导入：{exc}'})
        elif provider == 'custom_http':
            if not row.get('baseUrl'):
                result.update({'status': 'FAILED', 'message': 'custom_http 必须配置 baseUrl'})
            else:
                result.update({'status': 'READY', 'message': 'custom_http 配置已保存；当前只验证格式，不自动联网请求'})
        else:
            result.update({'status': 'FAILED', 'message': '未知 provider'})
    except Exception as exc:
        result.update({'status': 'FAILED', 'message': str(exc)})
    return payload(status=result['status'], source='local_api_config_test', data=result)
