# SPDX-License-Identifier: Apache-2.0
"""Bounded local calculations and proposed authenticated plan execution."""
import argparse
import json
import sys
import calculation
import key_binding

# No production trust root has been supplied. Do not accept plans until provisioned.
PINNED_PUBLIC_KEY = None
MAX_PLAN_BYTES = 65536

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def run_plan(envelope, secure_store, now=None):
    if PINNED_PUBLIC_KEY is None:
        raise ValueError('plan signing key unavailable')
    if len(canonical(envelope)) > MAX_PLAN_BYTES:
        raise ValueError('plan too large')
    plan = key_binding.verify(envelope, PINNED_PUBLIC_KEY, secure_store, now=now)
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
