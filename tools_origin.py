# SPDX-License-Identifier: Apache-2.0
"""Bounded local calculations and proposed authenticated plan execution."""
import argparse
import json
import hashlib
import os
import stat
import sys
import calculation
import key_binding

MAX_PLAN_BYTES = 65536

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def load_trust_root(path, expected_sha256):
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(c not in '0123456789abcdef' for c in expected_sha256):
        raise ValueError('trust root pin required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != 32:
            raise ValueError('invalid trust root')
        public = os.read(fd, 33)
        if len(public) != 32 or hashlib.sha256(public).hexdigest() != expected_sha256:
            raise ValueError('trust root mismatch')
        return public
    finally:
        os.close(fd)

def run_plan(envelope, secure_store, trust_root_path, trust_root_sha256, now=None):
    public_key = load_trust_root(trust_root_path, trust_root_sha256)
    if len(canonical(envelope)) > MAX_PLAN_BYTES:
        raise ValueError('plan too large')
    plan = key_binding.verify(envelope, public_key, secure_store, now=now)
    if set(plan) != {'key_ref', 'device_ref', 'iat', 'exp', 'plan_id', 'operation'}:
        raise ValueError('plan refused')
    operation = plan['operation']
    if not isinstance(operation, dict) or set(operation) != {'type', 'values', 'unit'} or operation['type'] != 'mean':
        raise ValueError('unsupported operation')
    return calculation.calculate(operation['values'], operation['unit'])

def outbound_approval(destination, payload):
    raise ValueError('outbound unavailable')

def main():
    parser = argparse.ArgumentParser(description='Run a bounded local calculation')
    parser.add_argument('action', choices=('mean',))
    parser.add_argument('--unit', required=True)
    parser.add_argument('values', nargs='+', type=float)
    args = parser.parse_args()
    try:
        print(json.dumps(calculation.calculate(args.values, args.unit), allow_nan=False))
    except (ValueError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
