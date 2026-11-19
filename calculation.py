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
    receipt = {'calculation': VERSION, 'input': json.loads(snapshot), 'input_sha256': hashlib.sha256(snapshot).hexdigest(), 'result': math.fsum(values) / len(values), 'unit': unit, 'absolute_tolerance': 0.0}
    receipt['receipt_sha256'] = hashlib.sha256(json.dumps(receipt, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return receipt

def rerun(receipt):
    try:
        if not isinstance(receipt, dict) or set(receipt) != {'calculation', 'input', 'input_sha256', 'result', 'unit', 'absolute_tolerance', 'receipt_sha256'}:
            return False
        if type(receipt['absolute_tolerance']) is not float or receipt['absolute_tolerance'] != 0.0:
            return False
        fresh = calculate(receipt['input']['values'], receipt['input']['unit'])
        # Recompute every field: a public digest is not an authentication signature.
        return receipt == fresh
    except (ValueError, TypeError, KeyError, OverflowError):
        return False

if __name__ == '__main__':
    import sys
    data = json.load(sys.stdin)
    print(json.dumps(calculate(data['values'], data['unit']), allow_nan=False))
