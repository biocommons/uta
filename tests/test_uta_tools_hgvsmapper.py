import unittest

from uta.db.transcriptdb import TranscriptDB
from uta.tools.hgvsmapper import HGVSMapper

class test_HGVSMapper(unittest.TestCase):

    def setUp(self):
        self.hgvsmapper = HGVSMapper( db = TranscriptDB(),
                                      cache_transcripts = True )

    def test_DNAH11(self):
        import csv
        tests_fn = 'tests/data/DNAH11.tsv'
        tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
        for rec in tests_in:
            if rec['rsid'].startswith('#'):
                continue
            if 'NM_003777.3' in rec['HGVSc']:
                print(rec)
                self.assertEqual(self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSg'])[:3],
                                 self.hgvsmapper.hgvs_to_genomic_coords(rec['HGVSc'])[:3] )

##    def xxx_test_garcia(self):
##        import csv
##        tests_fn = 'tests/data/garcia.tsv'
##        tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')
##        for test_rec in tests_in:
##            if test_rec['Gene'].startswith('#'):
##                continue
##            g_hgvs = test_rec['Genomic_position']
##            g_chrom,g_start,g_end,_ = self.hgvsmapper.hgvs_to_genomic_coords(g_hgvs)
##            g_loc = (g_chrom,g_start,g_end)
##            for c_hgvs in [test_rec['Mapping1'], test_rec['Mapping2']]:
##                c_chrom,c_start,c_end,_ = self.hgvsmapper.hgvs_to_genomic_coords(c_hgvs)
##                c_loc = (c_chrom,c_start,c_end)
##                self.assertEqual( g_loc, c_loc, "{g_hgvs} ~ {c_hgvs} => {g_loc} ~ {c_loc}".format(
##                    g_hgvs=g_hgvs,c_hgvs=c_hgvs,g_loc=g_loc,c_loc=c_loc) )



if __name__ == '__main__':
    unittest.main()
