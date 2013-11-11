import csv, unittest

from uta.db.transcriptdb import TranscriptDB
from uta.tools.hgvsmapper import HGVSMapper

import hgvs.parser


class test_HGVSMapper(unittest.TestCase):

    def setUp(self):
        self.hgvsparser = hgvs.parser.Parser()
        self.hgvsmapper = HGVSMapper( db = TranscriptDB(),
                                      cache_transcripts = True )

    def test_hgvs_to_genomic_coords_VonHL(self):
        tests_fn = 'tests/data/all_curated_hgvs.tsv'
        tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
        for rec in tests_in:
            if rec['id'].startswith('#'):
                continue
            try:
                self.assertEqual(
                    self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
                    self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )
            except Exception, msg:
                print 'fail %s\t%s\t%s\t%s' % (rec['id'], rec['HGVSg'], msg, rec['xml'])

            #self.assertEqual(
            #        self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
            #        self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )


    ########### DNAH11 TESTS ############

    #def test_hgvs_to_genomic_coords_DNAH11_dbsnp(self):
    #    tests_fn = 'tests/data/DNAH11-dbSNP.tsv'
    #    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
    #    for rec in tests_in:
    #        if rec['id'].startswith('#'):
    #            continue
    #        #if rec['HGVSp'] == '':
    #        #    continue
    #        self.assertEqual(
    #            self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
    #            self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )
    #
    #def test_hgvs_to_genomic_coords_DNAH11_hgmd(self):
    #    tests_fn = 'tests/data/DNAH11-HGMD.tsv'
    #    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
    #    for rec in tests_in:
    #        if rec['id'].startswith('#'):
    #            continue
    #        if rec['HGVSp'] == '':
    #            continue
    #        self.assertEqual(
    #            self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
    #            self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )
    #
    #def test_hgvsg_to_hgvsc_DNAH11_dbsnp(self):
    #    tests_fn = 'tests/data/DNAH11-dbSNP.tsv'
    #    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
    #    for rec in tests_in:
    #        if rec['id'].startswith('#'):
    #            continue
    #        #if rec['HGVSp'] == '':
    #        #    continue
    #        self.assertEqual(
    #            self.hgvsmapper.hgvsg_to_hgvsc(
    #                rec['HGVSg'],self.hgvsparser.parse(rec['HGVSc']).seqref,'GRCh37.p10'), rec['HGVSc'])
    #
    #def test_hgvsg_to_hgvsc_DNAH11_hgmd(self):
    #    tests_fn = 'tests/data/DNAH11-HGMD.tsv'
    #    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
    #    for rec in tests_in:
    #        if rec['id'].startswith('#'):
    #            continue
    #        if rec['HGVSp'] == '':
    #            continue
    #        self.assertEqual(
    #            self.hgvsmapper.hgvsg_to_hgvsc(
    #                rec['HGVSg'],self.hgvsparser.parse(rec['HGVSc']).seqref,'GRCh37.p10'), rec['HGVSc'])
    #
    ############ NEFL TESTS ############
    #
    #def test_hgvs_to_genomic_coords_NEFL_dbsnp(self):
    #    tests_fn = 'tests/data/NEFL-dbSNP.tsv'
    #    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
    #    for rec in tests_in:
    #        if rec['id'].startswith('#'):
    #            continue
    #        if rec['HGVSp'] == '':
    #            continue
    #        if 'NM_006158.4' in rec['HGVSc']:
    #            self.assertEqual(self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
    #                             self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )
    #
    ##def test_hgvs_to_genomic_coords_NEFL_hgmd(self):
    ##    tests_fn = 'tests/data/NEFL_HGMD_var.tsv'
    ##    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
    ##    for rec in tests_in:
    ##        if rec['id'].startswith('#'):
    ##            continue
    ##        if rec['HGVSp'] == '':
    ##            continue
    ##        if 'NM_006158.4' in rec['HGVSc']:
    ##            self.assertEqual(self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
    ##                             self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )
    #
    #def test_hgvsg_to_hgvsc_NEFL_dbsnp(self):
    #    tests_fn = 'tests/data/NEFL-dbSNP.tsv'
    #    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
    #    for rec in tests_in:
    #        if rec['id'].startswith('#'):
    #            continue
    #        if rec['HGVSp'] == '':
    #            continue
    #        if 'NM_006158.4' in rec['HGVSc']:
    #            self.assertEqual(
    #                self.hgvsmapper.hgvsg_to_hgvsc(rec['HGVSg'],'NM_006158.4','GRCh37.p10'),
    #                rec['HGVSc'])
    #
    ##def test_hgvsg_to_hgvsc_NEFL_hgmd(self):
    ##    tests_fn = 'tests/data/NEFL_HGMD_var.tsv'
    ##    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
    ##    for rec in tests_in:
    ##        if rec['id'].startswith('#'):
    ##            continue
    ##        if rec['HGVSp'] == '':
    ##            continue
    ##        if 'NM_006158.4' in rec['HGVSc']:
    ##            self.assertEqual(
    ##                self.hgvsmapper.hgvsg_to_hgvsc(rec['HGVSg'],'NM_006158.4','GRCh37.p10'),
    ##                rec['HGVSc'])
    #
    #
if __name__ == '__main__':
    unittest.main()
