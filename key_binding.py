# SPDX-License-Identifier: Apache-2.0
"""PROPOSED key/device binding; awaiting the server contract and trust root."""
import hashlib
import hmac
import json
import time
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def verify(envelope, public_key, secure_store, now=None):
    """secure_store supplies secret bytes via get_key() and get_install_id()."""
    try:
        if set(envelope) != {'plan', 'signature'}:
            raise ValueError
        plan = envelope['plan']
        if not isinstance(plan, dict):
            raise ValueError
        encoded = json.dumps(plan, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
        Ed25519PublicKey.from_public_bytes(public_key).verify(bytes.fromhex(envelope['signature']), encoded)
        key = secure_store.get_key()
        device = secure_store.get_install_id()
        if not isinstance(key, bytes) or not key or not isinstance(device, bytes) or not device:
            raise ValueError
        for field, value in (('key_ref', key), ('device_ref', device)):
            if not isinstance(plan.get(field), str) or not hmac.compare_digest(plan[field], hashlib.sha256(value).hexdigest()):
                raise ValueError
        now = int(time.time()) if now is None else now
        if type(plan.get('iat')) is not int or type(plan.get('exp')) is not int or not plan['iat'] <= now < plan['exp']:
            raise ValueError
        if not isinstance(plan.get('plan_id'), str) or not plan['plan_id'] or len(plan['plan_id']) > 256:
            raise ValueError
        return plan
    except (TypeError, ValueError, KeyError, InvalidSignature):
        raise ValueError('plan refused') from None


def refusal_message(status, body):
    if status == 403 and isinstance(body, dict) and body.get('error') == 'licensed_key_required':
        return 'A licensed key is required.'
    return 'Request could not be completed.'
