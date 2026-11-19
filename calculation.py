# SPDX-License-Identifier: Apache-2.0
"""A local, deterministic mean calculation and repeatability receipt."""
import hashlib
import json
import math

VERSION = 'mean/1'
MAX_VALUES = 10000

def calculate(values, unit):
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_VALUES:
        raise ValueError('supply between 1 and 10000 values')
    if not isinstance(unit, str) or not unit or len(unit) > 100:
        raise ValueError('unit required')
    if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in values):
        raise ValueError('finite numbers required')
    snapshot = json.dumps({'values': values, 'unit': unit}, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'calculation': VERSION, 'input': json.loads(snapshot), 'input_sha256': hashlib.sha256(snapshot).hexdigest(), 'result': math.fsum(values) / len(values), 'unit': unit, 'absolute_tolerance': 0.0}

def rerun(receipt):
    fresh = calculate(receipt['input']['values'], receipt['input']['unit'])
    if receipt['calculation'] != VERSION or receipt['input_sha256'] != fresh['input_sha256']:
        return False
    return math.isclose(fresh['result'], receipt['result'], rel_tol=0.0, abs_tol=receipt['absolute_tolerance'])

if __name__ == '__main__':
    import sys
    data = json.load(sys.stdin)
    print(json.dumps(calculate(data['values'], data['unit']), allow_nan=False))
