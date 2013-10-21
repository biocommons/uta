import csv, unittest

from uta.db.transcriptdb import TranscriptDB
from uta.tools.hgvsmapper import HGVSMapper

import hgvs.parser

class test_HGVSMapper(unittest.TestCase):

    def setUp(self):
        self.hgvsparser = hgvs.parser.Parser()
        self.hgvsmapper = HGVSMapper( db = TranscriptDB(),
                                      cache_transcripts = True )

    def test_hgvs_to_genomic_coords_DNAH11_dbsnp(self):
        tests_fn = 'tests/data/DNAH11-dbSNP.tsv'
        tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
        for rec in tests_in:
            if rec['id'].startswith('#'):
                continue
            if rec['HGVSp'] == '':
                continue
            self.assertEqual(
                self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
                self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )

    def test_hgvs_to_genomic_coords_DNAH11_hgmd(self):
        tests_fn = 'tests/data/DNAH11-HGMD.tsv'
        tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
        for rec in tests_in:
            if rec['id'].startswith('#'):
                continue
            if rec['HGVSp'] == '':
                continue
            self.assertEqual(
                self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
                self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )

    def test_hgvsg_to_hgvsc_DNAH11_dbsnp(self):
        tests_fn = 'tests/data/DNAH11-dbSNP.tsv'
        tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
        for rec in tests_in:
            if rec['id'].startswith('#'):
                continue
            if rec['HGVSp'] == '':
                continue
            self.assertEqual(
                self.hgvsmapper.hgvsg_to_hgvsc(
                    rec['HGVSg'],self.hgvsparser.parse(rec['HGVSc']).seqref,'GRCh37.p10'),
                rec['HGVSc'])

    def test_hgvsg_to_hgvsc_DNAH11_hgmd(self):
        tests_fn = 'tests/data/DNAH11-HGMD.tsv'
        tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
        for rec in tests_in:
            if rec['id'].startswith('#'):
                continue
            if rec['HGVSp'] == '':
                continue
            self.assertEqual(
                self.hgvsmapper.hgvsg_to_hgvsc(
                    rec['HGVSg'],self.hgvsparser.parse(rec['HGVSc']).seqref,'GRCh37.p10'),
                rec['HGVSc'])

if __name__ == '__main__':
    unittest.main()
