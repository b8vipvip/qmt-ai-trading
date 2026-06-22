from qmt_ai_trading.common.artifact_registry import ArtifactPathRegistry

def test_canonical_and_legacy_mapping(tmp_path):
    reg=ArtifactPathRegistry(tmp_path)
    assert reg.canonical_path('local_console_app',87).as_posix().endswith('artifacts/console_apps/stage87')
    assert reg.legacy_paths('market_gateway',84)[0].as_posix().endswith('local_console_market_stage84')

def test_resolve_falls_back_to_legacy(tmp_path):
    legacy=tmp_path/'local_console_market_stage84'; legacy.mkdir()
    reg=ArtifactPathRegistry(tmp_path)
    assert reg.resolve('market_gateway',84) == legacy
