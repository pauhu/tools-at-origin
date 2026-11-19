# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
import unittest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import key_binding as b

class Store:
 def __init__(self, key, device): self.key, self.device = key, device
 def get_key(self): return self.key
 def get_install_id(self): return self.device

class Tests(unittest.TestCase):
 def test_bound_and_refusals(self):
  key = Ed25519PrivateKey.generate()
  public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
  store = Store(b'test-key', b'test-install')
  plan = {'key_ref':hashlib.sha256(store.key).hexdigest(), 'device_ref':hashlib.sha256(store.device).hexdigest(), 'iat':1, 'exp':10, 'plan_id':'fixture'}
  enc = json.dumps(plan, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
  env = {'plan':plan, 'signature':key.sign(enc).hex()}
  self.assertEqual(b.verify(env, public, store, now=2)['plan_id'], 'fixture')
  for other in [Store(b'wrong',store.device), Store(store.key,b'other')]:
   with self.assertRaisesRegex(ValueError, 'plan refused'): b.verify(env,public,other,now=2)
  with self.assertRaises(ValueError): b.verify(env,public,store,now=10)
  plan['plan_id'] = 'altered'
  with self.assertRaises(ValueError): b.verify(env,public,store,now=2)
  self.assertEqual(b.refusal_message(403, {'error':'licensed_key_required'}),'A licensed key is required.')
