from __future__ import annotations
import time
from .models import AiModelInfo,AiModelDiscoveryResult,AiProviderConfig,to_dict
from .provider_client import ProviderClient
from .safety import mask_api_key, assert_no_api_key_in_report
LATEST_DISCOVERY={}
def _urls(base): return [base+'/models'] if base.endswith('/v1') else [base+'/v1/models', base+'/models']
def discover_models(provider_type, base_url, api_key='', timeout_seconds=60):
    client=ProviderClient(base_url,api_key,timeout_seconds); start=time.perf_counter(); last=''
    for url in _urls(client.base_url):
        status,data,elapsed=client.request_json('GET',url)
        if 200<=status<300 and isinstance(data.get('data'),list):
            models=[AiModelInfo(model_id=str(x.get('id','')), object=x.get('object','model'), owned_by=x.get('owned_by','unknown'), created=x.get('created'), raw=x, supports_chat=True, supports_responses='response' in str(x.get('id','')).lower()) for x in data['data'] if x.get('id')]
            models.sort(key=lambda m:m.model_id)
            provider=to_dict(AiProviderConfig('session',provider_type,client.base_url,mask_api_key(api_key),timeout_seconds))
            res=AiModelDiscoveryResult(True,provider_type,client.base_url,len(models),models,None,elapsed,provider)
            LATEST_DISCOVERY.clear(); LATEST_DISCOVERY.update(to_dict(res)); assert_no_api_key_in_report(LATEST_DISCOVERY,api_key); return res
        last=f'{status}: {data}'
    res=AiModelDiscoveryResult(False,provider_type,client.base_url,0,[],last,int((time.perf_counter()-start)*1000),{'api_key_masked':mask_api_key(api_key)})
    LATEST_DISCOVERY.clear(); LATEST_DISCOVERY.update(to_dict(res)); assert_no_api_key_in_report(LATEST_DISCOVERY,api_key); return res
