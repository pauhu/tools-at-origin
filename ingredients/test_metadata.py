# SPDX-License-Identifier: Apache-2.0
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
here=Path(__file__).parent
spec=importlib.util.spec_from_file_location('sbom_generate',here/'sbom_generate.py');sbom=importlib.util.module_from_spec(spec);spec.loader.exec_module(sbom)
spec2=importlib.util.spec_from_file_location('measure',here/'measure.py');measure=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(measure)
class MetadataControls(unittest.TestCase):
 def test_receipt_matches_calorie_rows(self):
  rows=(here/'calories.tsv').read_text().splitlines();receipt=(here/'ACCEPTANCE-RUN.txt').read_text().splitlines()
  self.assertIn('Measurement columns: '+rows[0],receipt)
  self.assertEqual([line.removeprefix('Measurement row: ') for line in receipt if line.startswith('Measurement row: ')],rows[1:])
 def test_distribution_checksum(self):
  record=json.loads((here/'dataset.jsonld').read_text());dist=record['dcat:distribution'];checksum=dist['spdx:checksum']
  self.assertNotIn('spdx:checksum',record)
  self.assertEqual(checksum['spdx:algorithm']['@id'],'http://spdx.org/rdf/terms#checksumAlgorithm_sha256')
  self.assertEqual(checksum['spdx:checksumValue']['@value'],measure.DATASET_SHA256)
  self.assertTrue(dist['dcat:accessURL']['@id'].endswith('/'+measure.REVISION+'/annotations/v3/raw/test.jsonl'))
 def test_lock_and_invalid(self):
  raw=(here.parent/'requirements.lock').read_bytes();self.assertEqual(len(sbom.build(raw)['components']),4)
  with self.assertRaises(ValueError):sbom.build(raw+b'unknown==1 --hash=sha256:'+b'0'*64+b'\n')
 def test_stale_source_and_output(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'calories.tsv').write_text('correct');import hashlib
   digest=hashlib.sha256(b'correct').hexdigest();(p/'manifest.json').write_text(json.dumps({'schema':measure.SCHEMA,'sources':{'a':'old'},'environment':{},'fixtures':[], 'outputs':{'calories.tsv':digest}}))
   with patch.object(measure,'OUT',p),patch.object(measure,'source_hashes',return_value={'a':'new'}):
    with self.assertRaisesRegex(ValueError,'stale_source'):measure.check()
   (p/'calories.tsv').write_text('changed')
   with patch.object(measure,'OUT',p),patch.object(measure,'source_hashes',return_value={'a':'old'}),patch.object(measure,'environment',return_value={}),patch.object(measure,'fixtures',return_value=[]):
    with self.assertRaisesRegex(ValueError,'stale_output'):measure.check()
if __name__=='__main__':unittest.main()
