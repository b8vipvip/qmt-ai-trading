from __future__ import annotations
import json
from pathlib import Path
from .artifact_registry import ArtifactPathRegistry

ROOTS=['artifacts/console_apps','artifacts/reports','artifacts/market_data','artifacts/validation','artifacts/runtime','legacy']

def build_migration_plan(repo_root: str | Path='.') -> dict:
    reg=ArtifactPathRegistry(repo_root)
    steps=[]
    for m in reg.as_dict()['mappings']:
        steps.append({'logical_name':m['logical_name'],'stage':m['stage'],'from_legacy':m['legacy'],'to_canonical':m['canonical'],'action':'PLAN_ONLY_NO_DELETE','destructive':False})
    return {'stage':'Stage87','plan_only':True,'delete_legacy':False,'move_all_history':False,'roots_to_create':ROOTS,'steps':steps}

def build_path_health(repo_root: str | Path='.') -> dict:
    root=Path(repo_root); reg=ArtifactPathRegistry(root); rows=[]
    for m in reg.as_dict()['mappings']:
        canonical=root/m['canonical']; legacy=[root/p for p in m['legacy']]
        rows.append({'logical_name':m['logical_name'],'stage':m['stage'],'canonical':m['canonical'],'canonical_exists':canonical.exists(),'legacy':m['legacy'],'legacy_exists':[p.exists() for p in legacy],'resolved':str(reg.resolve(m['logical_name'], m['stage']).relative_to(root) if reg.resolve(m['logical_name'], m['stage']).is_relative_to(root) else reg.resolve(m['logical_name'], m['stage']))})
    return {'stage':'Stage87','read_strategy':'canonical_first_then_legacy','delete_legacy':False,'paths':rows}

def write_json_if_changed(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True); text=json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)
    if not path.exists() or path.read_text(encoding='utf-8') != text: path.write_text(text,encoding='utf-8')

def write_md_if_changed(path: Path, title: str, data: dict):
    text='# '+title+'\n\n```json\n'+json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n```\n'
    if not path.exists() or path.read_text(encoding='utf-8') != text: path.write_text(text,encoding='utf-8')

def run_artifact_migration_stage87(repo_root='.', output_dir='local_console_artifact_migration_stage87') -> dict:
    root=Path(repo_root); out=root/output_dir
    for rel in ROOTS: (root/rel).mkdir(parents=True, exist_ok=True)
    registry=ArtifactPathRegistry(root).as_dict(); plan=build_migration_plan(root); compat={'stage':'Stage87','compatibility_preserved':True,'canonical_first':True,'legacy_fallback':True,'no_legacy_delete':True,'mappings':registry['mappings']}; health=build_path_health(root)
    report={'stage':'Stage87','status':'SUCCESS','task_id':'artifact_migration_plan','output_dir':output_dir,'plan_only':True,'destructive_moves':False,'delete_legacy':False,'canonical_roots':ROOTS,'compatibility_preserved':True,'registry_count':len(registry['mappings'])}
    files={'artifact_registry':registry,'artifact_migration_plan':plan,'artifact_compatibility_map':compat,'artifact_path_health':health,'artifact_migration_report':report}
    for n,d in files.items(): write_json_if_changed(out/f'{n}.json',d); write_md_if_changed(out/f'{n}.md',n,d)
    return report
