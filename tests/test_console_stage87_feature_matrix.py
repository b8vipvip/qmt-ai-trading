from pathlib import Path

JS = Path('local_console_app_stage87/app.js').read_text(encoding='utf-8')


def test_feature_matrix_exists_with_required_columns_and_status_enums():
    assert '前端功能矩阵 / Feature Matrix' in JS
    for column in ['模块名称','前端页面状态','后端 API 状态','数据源路径','是否可交互','是否 dry-run','是否 read-only','当前是否占位','下一步动作']:
        assert column in JS
    for status in ['INTERACTIVE','STATIC_PLACEHOLDER','BACKEND_MISSING','API_ERROR','DATA_MISSING']:
        assert status in JS


def test_backend_missing_pages_are_explicitly_marked():
    assert '状态：后端待开发' in JS
    assert '当前页面：仅占位' in JS
    assert '预计后端接口' in JS
    assert '需要实现' in JS
