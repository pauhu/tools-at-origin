# SPDX-License-Identifier: Apache-2.0
import importlib.util
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('ingredients_measure',Path(__file__).parent/'measure.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Controls(unittest.TestCase):
 def test_network_detected(self):
  self.assertEqual(m.parse_trace('1 connect(3, {}, 16) = -1 ECONNREFUSED\n')[2],1)
  self.assertEqual(m.parse_trace('1 read(3, "a", 1) = 1\n')[2],0)
 def test_changed_revision_refused(self):
  import dataset_fixture
  data=b'fixture'
  with patch.object(dataset_fixture,'SIZE',len(data)), patch.object(dataset_fixture,'FILE_SHA256',hashlib.sha256(data).hexdigest()):
   self.assertEqual(dataset_fixture.verify(data),data)
   with self.assertRaisesRegex(ValueError,'dataset_pin_mismatch'):dataset_fixture.verify(data,revision='0'*40)
 def test_operation_refuses_network(self):
  from unittest.mock import patch, MagicMock
  with patch.object(m.shutil,'which',return_value='/bin/true'), patch.object(m.Path,'is_file',return_value=True), patch.object(m.subprocess,'run',return_value=MagicMock(returncode=0)), patch.object(m.Path,'read_text',return_value='1 connect(3, {}, 16) = -1 ECONNREFUSED\n'):
   with self.assertRaisesRegex(ValueError,'fixture_network_forbidden'):m.run_fixture('fixture','mean','/tmp/data')
 def test_real_pinned_sample_if_supplied(self):
  import os, dataset_fixture
  sample=os.environ.get('INGREDIENTS_SAMPLE')
  if not sample:self.skipTest('provide previously fetched pinned sample')
  self.assertEqual(len(dataset_fixture.verify(Path(sample).read_bytes())),dataset_fixture.SIZE)
 def test_missing_instrumentation(self):
  with self.assertRaisesRegex(ValueError,'instrumentation_missing'):m.run_fixture('fixture','x',exe='/path/not/present')
 def test_fixture_failure(self):
  with self.assertRaisesRegex(ValueError,'fixture_failed'):m.run_fixture('fixture','nonexistent_fixture_module')
 def test_read_write_parser(self):
  self.assertEqual(m.parse_trace('1 read(3, "x", 1) = 1\n2 write(1, "ab", 2) = 2\n'),(1,2,0))
if __name__=='__main__':unittest.main()
