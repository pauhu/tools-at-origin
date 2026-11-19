# SPDX-License-Identifier: Apache-2.0
"""Measure named offline fixture runs; integrity checks do not prove provenance."""
import hashlib, importlib.metadata, json, os, platform, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'ingredients'
EXCLUDE={'ingredients/README.md','ingredients/calories.tsv','ingredients/manifest.json'}
SCHEMA='2.0'
DATASET='n4ze3m/tiny-voca'
REVISION='63b6b89622e984d7c7a0799ca4b4c443dd5f48b2'
DATASET_ID=DATASET+'@'+REVISION
LICENCE='CC-BY-4.0'
DATASET_SHA256='89874e24611017ad18e24836fc018272d4e5723218f2dcbba3ca3619eaa145ce'
SAMPLE_BYTES=383110

def source_hashes():
    paths=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z']).decode().split('\0')
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths if p and p not in EXCLUDE}

def fixtures():
    if (ROOT/'origin_cli.py').exists():return [[DATASET_ID,'fetch'],[DATASET_ID,'cite']]
    if (ROOT/'tools_origin.py').exists():return [[DATASET_ID,'mean']]
    raise ValueError('fixture_definition_missing')

def deps():
    pyproject=ROOT/'pyproject.toml'
    if pyproject.exists():
        text=pyproject.read_text(); project=re.search(r'(?ms)^\[project\]\s*$([\s\S]*?)(?=^\[|\Z)',text)
        if not project or not re.search(r'(?m)^dependencies\s*=\s*\[\s*\]\s*$',project.group(1)):raise ValueError('pyproject_dependencies_unknown')
    req=ROOT/'requirements.txt';declared={}
    if req.exists():
        for line in req.read_text().splitlines():
            if not line.strip() or line.startswith('#'):continue
            match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9.]+)',line.strip())
            if not match:raise ValueError('dependency_unpinned')
            declared[match.group(1).lower().replace('_','-')]=match.group(2)
    packages=[]
    for name,version in sorted(declared.items()):
        m=importlib.metadata.metadata(name)
        if m['Version']!=version:raise ValueError('dependency_version_mismatch_'+name)
        licence=m.get('License-Expression') or m.get('License')
        if not licence or '\n' in licence:raise ValueError('dependency_licence_unknown_'+name)
        for dep in importlib.metadata.requires(name) or []:
            if 'extra ==' in dep:continue
            match=re.match(r'^([A-Za-z0-9_.-]+)',dep)
            if not match:raise ValueError('dependency_parse')
            child=match.group(1).lower().replace('_','-')
            if child not in declared:raise ValueError('transitive_dependency_unpinned_'+child)
        packages.append({'name':name,'version':version,'licence':licence})
    return packages

def environment():
    exe=shutil.which('strace');timer='/usr/bin/time'
    if not exe or not Path(timer).is_file():raise ValueError('instrumentation_missing')
    return {'python':platform.python_version(),'implementation':platform.python_implementation(),'system':platform.system(),'release':platform.release(),'machine':platform.machine(),'strace':subprocess.check_output([exe,'--version'],text=True).splitlines()[0], 'time_sha256':hashlib.sha256(Path(timer).read_bytes()).hexdigest(),'dependencies':deps()}

def parse_trace(lines):
    read=write=network=0
    for line in lines.splitlines():
        if re.search(r'\b(connect|sendto|sendmsg)\(',line):network+=1
        m=re.search(r'(?:\b(read|write)\(|<\.\.\. (read|write) resumed>).*\)\s+=\s+(\d+)(?:\s|$)',line)
        if m:
            if (m.group(1) or m.group(2))=='read':read+=int(m.group(3))
            else:write+=int(m.group(3))
    return read,write,network

def run_fixture(fixture_id,test,sample=None,exe=None):
    tracer=exe or shutil.which('strace');timer='/usr/bin/time'
    if not tracer or not Path(tracer).is_file() or not Path(timer).is_file():raise ValueError('instrumentation_missing')
    with tempfile.TemporaryDirectory() as temp:
        trace=Path(temp)/'trace';mem=Path(temp)/'mem';start=time.monotonic_ns()
        p=subprocess.run([tracer,'-f','-qq','-e','trace=read,write,connect,sendto,sendmsg','-o',str(trace),timer,'-f','%M','-o',str(mem),sys.executable,str(OUT/'dataset_fixture.py'),test,str(sample or '')],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
        elapsed=(time.monotonic_ns()-start)/1e6
        if p.returncode:raise ValueError('fixture_failed_'+fixture_id)
        rb,wb,net=parse_trace(trace.read_text())
        if net:raise ValueError('fixture_network_forbidden_'+fixture_id)
        return f'{SCHEMA}\t{fixture_id}\t{test}\t{LICENCE}\t{SAMPLE_BYTES}\t{DATASET_SHA256}\t{elapsed:.3f}\t{int(mem.read_text().strip())/1024:.3f}\t{rb}\t{wb}\t{net}\t0'

def check():
    m=json.loads((OUT/'manifest.json').read_text())
    if m['schema']!=SCHEMA or m['sources']!=source_hashes():raise ValueError('stale_source')
    if m['environment']!=environment() or m['fixtures']!=fixtures():raise ValueError('stale_environment')
    for name,digest in m['outputs'].items():
        if hashlib.sha256((OUT/name).read_bytes()).hexdigest()!=digest:raise ValueError('stale_output')
    print('INGREDIENTS=MET scope=integrity_and_environment_not_provenance')

def measure(sample):
    import dataset_fixture
    dataset_fixture.verify(Path(sample).read_bytes())
    files=source_hashes();env=environment();modules=sorted(p for p in files if p.endswith(('.py','.mjs')) and not p.startswith('ingredients/'));data=sorted(p for p in files if p.lower().endswith(('.json','.csv','.tsv','.jsonl','.xml','.txt')) and p!='requirements.txt' and not p.startswith('ingredients/'))
    readme=['# Ingredients: measured resources','','Dataset: '+DATASET+' at revision '+REVISION+'; licence '+LICENCE+'; file SHA-256 '+DATASET_SHA256+'; sample size '+str(SAMPLE_BYTES)+' bytes. Source and attribution: https://huggingface.co/datasets/'+DATASET+'. Creator: Muhammed Nazeem. Licence: https://creativecommons.org/licenses/by/4.0/. The sample is unmodified; this measurement reads durations from its first ten records. Fetch and verify the sample separately; it is not committed.','', 'The operation measurement starts a fresh Python interpreter and includes interpreter startup, loading and reading the local sample, calculation and output, plus tracing overhead. The separate fixture fetch is not counted. Attempts of connect, sendto and sendmsg must be zero; other network syscalls and socket writes are not counted, so this is not proof of zero network activity. To reproduce, run python ingredients/dataset_fixture.py fetch-sample PATH once, then run python ingredients/measure.py --measure PATH in the documented environment; timings will vary. --check verifies integrity and environment only, not measurement provenance. SBOM hashes are lockfile distribution hashes, not verified installed-artifact hashes.','', 'Repository licence: Apache-2.0.','','## Declared dependencies and licences','']
    readme+=['- '+x['name']+' '+x['version']+'; licence: '+x['licence'] for x in env['dependencies']] or ['- Python standard library only.']
    readme+=['','## Modules','']+['- `'+p+'`' for p in modules]+['','## Bundled data','']
    readme+=['- `'+p+'`; SHA-256 `'+files[p]+'`; origin: tracked repository file (original publisher not established).' for p in data] or ['- No bundled data files identified by the supported extensions.']
    (OUT/'README.md').write_text('\n'.join(readme)+'\n')
    rows=['schema\tfixture_id\toperation\tlicence\tsample_bytes\tfile_sha256\twall_ms\tpeak_rss_mib\tbytes_read\tbytes_written\tconnect_sendto_sendmsg_attempts\tmodel_tokens']+[run_fixture(name,test,sample) for name,test in fixtures()]
    (OUT/'calories.tsv').write_text('\n'.join(rows)+'\n')
    outputs={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ('README.md','calories.tsv')}
    (OUT/'manifest.json').write_text(json.dumps({'schema':SCHEMA,'sources':files,'environment':env,'fixtures':fixtures(),'outputs':outputs},sort_keys=True,indent=2)+'\n');check()
if __name__=='__main__':
    try:
        if sys.argv[1:]==['--check']:check()
        elif len(sys.argv)==3 and sys.argv[1]=='--measure':measure(sys.argv[2])
        else:raise ValueError('use --check or --measure SAMPLE')
    except (OSError,ValueError,subprocess.SubprocessError,KeyError,json.JSONDecodeError,importlib.metadata.PackageNotFoundError) as e:
        print('INGREDIENTS=MISS reason='+str(e).replace(' ','_'));sys.exit(1)
