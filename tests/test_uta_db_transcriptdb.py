import unittest

from uta.db.transcriptdb import TranscriptDB

class Test_transcriptdb(unittest.TestCase):
    def setUp(self):
        self.db = TranscriptDB()

    def test_transcriptdb_get_tx_for_gene(self):
        tis = self.db.get_tx_for_gene('MCL1')
        self.assertEquals( len(tis), 3 )
        self.assertEquals( set([ti['ac'] for ti in tis]),
                           set(('NM_001197320.1','NM_021960.4','NM_182763.2')) )

    def Test_transcriptdb_get_tx_info(self):
        self.assertIsNone( self.db.get_tx_info('bogus') )
        self.assertIsNotNone( self.db.get_tx_info('NM_001197320.1') )

        ti = self.db.get_tx_info('NM_001197320.1')
        self.assertEquals(ti['ac'], 'NM_001197320.1')

    def Test_transcriptdb_get_tx_exons(self):
        self.assertEquals( self.db.get_tx_exons('bogus','GRCh37.p10')    , [])
        self.assertEquals( self.db.get_tx_exons('NM_001197320.1','bogus'), [] )

        exons = self.db.get_tx_exons('NM_001197320.1', 'GRCh37.p10')
        self.assertEquals(len(exons), 4)


if __name__ == '__main__':
    unittest.main()
