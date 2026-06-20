from .preview_models import PreviewRoute, LocalConsolePreviewRouteType as T
ALLOWED_ROUTE_SPECS=[('/',T.STATIC_HTML),('/index.html',T.STATIC_HTML),('/app.js',T.STATIC_JS),('/style.css',T.STATIC_CSS),('/data_bundle.json',T.STATIC_JSON),('/binding_manifest.json',T.STATIC_JSON),('/data_source_map.json',T.STATIC_JSON),('/static_data_safety.json',T.STATIC_JSON),('/health',T.HEALTH),('/preview-safety',T.SAFETY),('/preview-manifest',T.MANIFEST)]
FORBIDDEN_ROUTES=['/order','/orders','/trade','/execute','/approve','/live','/notify','/account','/positions','/assets']
FORBIDDEN_HASH_ROUTES=['#/order','#/orders','#/trade','#/execute','#/approve','#/live','#/notify','#/account','#/positions','#/assets']
def build_allowed_preview_routes(): return [PreviewRoute(path=p,route_type=t) for p,t in ALLOWED_ROUTE_SPECS]
