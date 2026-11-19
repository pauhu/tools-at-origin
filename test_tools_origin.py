# SPDX-License-Identifier: Apache-2.0
import hashlib
import socket
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import tools_origin as t

class Store:
    def get_key(self): return b'fixture-only-high-entropy-key'
    def get_install_id(self): return b'fixture-installation'

class Tests(unittest.TestCase):
    def setUp(self):
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'trust.pub'; self.root.write_bytes(self.public)
        self.pin = hashlib.sha256(self.public).hexdigest()
        self.store = Store()
        self.plan = {'key_ref':hashlib.sha256(self.store.get_key()).hexdigest(), 'device_ref':hashlib.sha256(self.store.get_install_id()).hexdigest(), 'iat':1, 'exp':10, 'plan_id':'fixture', 'operation':{'type':'mean','values':[1,2,6],'unit':'m'}}
    def envelope(self):
        return {'plan':self.plan,'signature':self.private.sign(t.canonical(self.plan)).hex()}
    def test_unprovisioned_key_refused(self):
        with self.assertRaises(OSError): t.run_plan(self.envelope(),self.store,self.root.with_name('missing'),self.pin,now=2)
        with self.assertRaisesRegex(ValueError,'mismatch'): t.run_plan(self.envelope(),self.store,self.root,'0'*64,now=2)
    def test_bound_plan_offline_and_tamper(self):
        with patch.object(socket,'socket',side_effect=AssertionError('network')):
            env=self.envelope();self.assertEqual(t.run_plan(env,self.store,self.root,self.pin,now=2)['result'],3)
            env['plan']['operation']['values']=[5]
            with self.assertRaises(ValueError):t.run_plan(env,self.store,self.root,self.pin,now=2)
    def test_forbidden_operation_even_when_signed(self):
        self.plan['operation']={'type':'command','values':[1],'unit':'m'}
        if True:
            with self.assertRaisesRegex(ValueError,'unsupported operation'):t.run_plan(self.envelope(),self.store,self.root,self.pin,now=2)
    def test_wrong_device_and_expiry(self):
        if True:
            env=self.envelope()
            with self.assertRaises(ValueError):t.run_plan(env,self.store,self.root,self.pin,now=10)
            with patch.object(self.store,'get_install_id',return_value=b'other'):
                with self.assertRaises(ValueError):t.run_plan(env,self.store,self.root,self.pin,now=2)
    def test_malformed_root(self):
        self.root.write_bytes(b'short')
        with self.assertRaisesRegex(ValueError,'invalid trust root'):t.run_plan(self.envelope(),self.store,self.root,self.pin,now=2)
    def test_malformed_and_oversized_plan_bytes(self):
        for raw in (b'{',b'['*70000):
            with self.assertRaises(ValueError):t.run_plan_bytes(raw,self.store,self.root,self.pin,now=2)
        self.assertEqual(t.run_plan_bytes(t.canonical(self.envelope()),self.store,self.root,self.pin,now=2)['result'],3)
    def test_operation_input_limit_signed(self):
        self.plan['operation']['values']=[1]*10001
        with self.assertRaises(ValueError):t.run_plan(self.envelope(),self.store,self.root,self.pin,now=2)
    def test_malformed_envelopes(self):
        for env in ({}, {'plan':{},'signature':'xx'}, {'plan':[],'signature':''}):
            with self.assertRaises(ValueError):t.run_plan(env,self.store,self.root,self.pin,now=2)
    def test_outbound_refused(self):
        with self.assertRaisesRegex(ValueError,'outbound unavailable'):t.outbound_approval('https://example.org',b'x')
    def test_no_external_runner(self):
        self.assertFalse(hasattr(t,'run_tool'))
