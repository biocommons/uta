import unittest

from uta.db.transcriptdb import TranscriptDB
from uta.tools.transcriptprojector import TranscriptProjector

class Test_transcriptdb(unittest.TestCase):
    def setUp(self):
        self.db = TranscriptDB()
        self.ref = 'GRCh37.p10'

    # Test combinations of these, both ways
    # MCL1, multiple transcripts, SNPs mapped by NCBI
    # http://tinyurl.com/len34jc
    # http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=12036617
    # NM_001197320.1:c.514G>A
    # NM_021960.4:c.973G>A
    # NM_182763.2:c.725G>A

    def test_20_60(self):
        pj = TranscriptProjector(self.db,self.ref,'NM_001197320.1','NM_021960.4')
        self.assertEquals( pj.map_forward(513,514), (972,973) )
        self.assertEquals( pj.map_backward(972,973), (513,514) )

    def test_20_63(self):
        pj = TranscriptProjector(self.db,self.ref,'NM_001197320.1','NM_182763.2')
        self.assertEquals( pj.map_forward(513,514), (724,725) )
        self.assertEquals( pj.map_backward(724,725), (513,514) )

    def test_60_63(self):
        pj = TranscriptProjector(self.db,self.ref,'NM_021960.4','NM_182763.2')
        self.assertEquals( pj.map_forward(972,973), (724,725) )
        self.assertEquals( pj.map_backward(724,725), (972,973) )

    def test_failures(self):
        self.assertRaises( RuntimeError, TranscriptProjector, self.db,self.ref,'NM_bogus','NM_bogus' )
        self.assertRaises( RuntimeError, TranscriptProjector, self.db,'bogus','NM_001197320.1','NM_021960.4' )
        

if __name__ == '__main__':
    unittest.main()
