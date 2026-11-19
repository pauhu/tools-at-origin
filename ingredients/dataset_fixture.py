# SPDX-License-Identifier: Apache-2.0
"""Run a named operation on a bounded, revision-pinned public dataset file."""
import hashlib,json,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
DATASET='n4ze3m/tiny-voca'
REVISION='63b6b89622e984d7c7a0799ca4b4c443dd5f48b2'
FILE='annotations/v3/raw/test.jsonl'
FILE_SHA256='89874e24611017ad18e24836fc018272d4e5723218f2dcbba3ca3619eaa145ce'
SIZE=383110
URL='https://huggingface.co/datasets/'+DATASET+'/raw/'+REVISION+'/'+FILE

def verify(data,revision=REVISION):
    if revision!=REVISION or len(data)!=SIZE or hashlib.sha256(data).hexdigest()!=FILE_SHA256:
        raise ValueError('dataset_pin_mismatch')
    return data

def read_data(mode):
    if mode in ('fetch','cite'):
        import origin
        result=origin.fetch(URL,limit=500000,timeout=30)
        if result['sha256']!=FILE_SHA256:raise ValueError('dataset_pin_mismatch')
        return result['text'].encode('utf-8'),result['fetched_at']
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*a,**kw):return None
    with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(URL,timeout=30) as response:
        if response.status!=200 or response.geturl()!=URL:raise ValueError('dataset_http')
        data=response.read(500001)
    return verify(data),None

def run(mode, sample=None):
    if mode == 'mean':
        if sample is None: raise ValueError('sample_missing')
        data, fetched = verify(Path(sample).read_bytes()), None
    else:
        data, fetched = read_data(mode)
    if mode=='fetch':return {'sha256':FILE_SHA256,'sample_bytes':SIZE}
    if mode=='cite':
        import origin_cli
        return origin_cli.cite({'sources':[{'title':'tiny-voca annotations','url':URL,'retrieved_at':fetched}]})
    if mode=='mean':
        import calculation
        rows=[json.loads(line) for line in data.splitlines()[:10]]
        values=[float(x) for row in rows for x in row['durations']][:1000]
        return calculation.calculate(values,'duration units')
    raise ValueError('fixture_operation')
if __name__=='__main__':
    try:
        if len(sys.argv)!=3 or sys.argv[1] not in ('mean','fetch-sample'):raise ValueError('fixture_operation')
        if sys.argv[1]=='fetch-sample':
            data,_=read_data('mean')
            with Path(sys.argv[2]).open('xb') as out:out.write(data)
            print('FIXTURE=MET')
        else:print(json.dumps(run(sys.argv[1],sys.argv[2]),allow_nan=False))
    except Exception as e:
        print('DATASET_FIXTURE=MISS reason='+type(e).__name__,file=sys.stderr);sys.exit(1)
