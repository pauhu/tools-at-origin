# SPDX-License-Identifier: Apache-2.0
"""Generate lock-derived CycloneDX metadata; unknown entries fail closed."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
LICENCES={'cryptography':'Apache-2.0 OR BSD-3-Clause','cffi':'MIT-0','pycparser':'BSD-3-Clause','typing-extensions':'PSF-2.0'}
def build(raw):
 components=[];seen=set()
 for line in raw.decode().splitlines():
  match=re.fullmatch(r'([a-z0-9-]+)==([0-9.]+) --hash=sha256:([0-9a-f]{64})',line)
  if not match:raise ValueError('invalid_lock_line')
  name,version,digest=match.groups()
  if name in seen or name not in LICENCES:raise ValueError('unknown_or_duplicate_dependency')
  seen.add(name);components.append({'type':'library','name':name,'version':version,'purl':'pkg:pypi/'+name+'@'+version,'hashes':[{'alg':'SHA-256','content':digest}],'licenses':[{'expression':LICENCES[name]}]})
 if seen!=set(LICENCES):raise ValueError('incomplete_lock')
 return {'bomFormat':'CycloneDX','specVersion':'1.7','version':1,'metadata':{'component':{'type':'application','name':'tools-at-origin','version':'0.1.3'},'properties':[{'name':'lock-sha256','value':hashlib.sha256(raw).hexdigest()},{'name':'generator','value':'sbom_generate.py/1'}]},'components':components}
if __name__=='__main__':
 raw=(ROOT/'requirements.lock').read_bytes();(ROOT/'ingredients/sbom.cdx.json').write_text(json.dumps(build(raw),sort_keys=True,indent=2)+'\n')
