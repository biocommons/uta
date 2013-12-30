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

    def Test_transcriptdb_get_tx_seq(self):
        self.assertIsNone( self.db.get_tx_seq('bogus') )
        self.assertTrue( self.db.get_tx_seq('NM_001197320.1').startswith('gcgcaaccctccggaag') )

    def Test_transcriptdb_get_tx_exons(self):
        self.assertEquals( self.db.get_tx_exons('bogus','GRCh37.p10')    , [])
        self.assertEquals( self.db.get_tx_exons('NM_001197320.1','bogus'), [] )

        exons = self.db.get_tx_exons('NM_001197320.1', 'GRCh37.p10')
        self.assertEquals(len(exons), 4)


if __name__ == '__main__':
    unittest.main()

## <LICENSE>
## Copyright 2014 UTA Contributors (https://bitbucket.org/invitae/uta)
## 
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
## 
##     http://www.apache.org/licenses/LICENSE-2.0
## 
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## </LICENSE>
