# SPDX-License-Identifier: Apache-2.0
import json
import subprocess
import sys
import unittest
from pathlib import Path
import calculation

class TestCalculation(unittest.TestCase):
 def test_cli_and_repeat(self):
  command = [sys.executable, str(Path(calculation.__file__))]
  result = subprocess.run(command, input='{"values":[1,2,6],"unit":"m"}', text=True, capture_output=True, check=True)
  record = json.loads(result.stdout)
  self.assertEqual(record['result'], 3)
  self.assertTrue(calculation.rerun(record))
  record['result'] = 4
  self.assertFalse(calculation.rerun(record))
  record['result'] = 999; record['absolute_tolerance'] = 1000.0
  self.assertFalse(calculation.rerun(record))
  record['receipt_sha256'] = '0' * 64
  self.assertFalse(calculation.rerun(record))
 def test_invalid_inputs(self):
  for values in ([], [float('nan')], [True], [1]*10001):
   with self.assertRaises(ValueError): calculation.calculate(values, 'm')

if __name__ == '__main__': unittest.main()
