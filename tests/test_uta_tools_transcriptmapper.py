import unittest

from uta.db.transcriptdb import TranscriptDB
from uta.exceptions import *
from uta.tools.transcriptmapper import TranscriptMapper

class Test_transcriptmapper(unittest.TestCase):
    ref = 'GRCh37.p10'

    def setUp(self):
        self.db = TranscriptDB()

    def test_transcriptmapper_failures(self):
        self.assertRaises(UTAError, TranscriptMapper, self.db,ref=self.ref,ac='bogus')
        self.assertRaises(UTAError, TranscriptMapper, self.db,ref='bogus',ac='NM_033089.6')

    # reece=> select * from uta.tx_info where ac='NM_033089.6';
    #   gene  | strand |     ac      | cds_start_i | cds_end_i |                 descr                 | summary 
    # --------+--------+-------------+-------------+-----------+---------------------------------------+---------
    #  ZCCHC3 |      1 | NM_033089.6 |          24 |      1236 | zinc finger, CCHC domain containing 3 | 
    # 
    # reece=> select * from uta.tx_exons where ac='NM_033089.6';
    #      ac      | ord | name | t_start_i | t_end_i |    ref     | g_start_i | g_end_i |    cigar    |                                                                                                                         
    # -------------+-----+------+-----------+---------+------------+-----------+---------+-------------+------------------------
    #  NM_033089.6 |   1 | 1    |         0 |    2759 | GRCh37.p10 |    278203 |  280965 | 484M3D2275M | GGAGGATGCTGGGAAGGAGGTAA
    def test_transcriptmapper_TranscriptMapper_1_ZCCHC3(self):
        ac = 'NM_033089.6'
        tm = TranscriptMapper(self.db,ac,self.ref)

        # http://tinyurl.com/mattx8u
        self.assertEquals( tm.g_to_r(278203,278203), (0,0) )
        self.assertEquals( tm.g_to_r(278203,278213), (0,10) )
        self.assertEquals( tm.r_to_g(0,0), (278203,278203) )
        self.assertEquals( tm.r_to_g(0,10), (278203,278213) )
        
        # http://tinyurl.com/kvrtkan
        # self.assertEquals( tm.g_to_r(2759,2759),(280965,280965)  )  # 0-width not supported
        self.assertEquals( tm.g_to_r(280955,280965), (2749,2759) )
        self.assertEquals( tm.r_to_g(2759,2759),(280965,280965)  )
        self.assertEquals( tm.r_to_g(2749,2759), (280955,280965) )
        
        # Around the deletion
        # http://tinyurl.com/jwt3txg
        # 687       690
        # C | C G G | C        
        #   \___ ___/
        #     C | C
        #      484
        self.assertEquals( tm.g_to_r(278686, 278687), (483,484) )
        self.assertEquals( tm.r_to_g(483,484), (278686, 278687) )
        # self.assertEquals( tm.r_to_g(484,484), (278687, 278690) ) # 0-width not supported yet
        self.assertEquals( tm.g_to_r(278690, 278691), (484,485) )
        self.assertEquals( tm.r_to_g(484,485), (278690, 278691) )

        # around cds_start (24) and cds_end (1236), mindful of *coding* del (3D)
        self.assertEquals( tm.r_to_c(24, 1236), (0,1236-24) )
        self.assertEquals( tm.c_to_r(0,1236-24), (24, 1236) )
        self.assertEquals( tm.g_to_c(278203+24,278203+1236), (0,1236-24-3) )
        self.assertEquals( tm.c_to_g(0,1236-24-3), (278203+24,278203+1236) )


    # reece=> select * from uta.tx_info where ac='NM_182763.2';
    #  gene | strand |     ac      | cds_start_i | cds_end_i |                      descr                      | 
    # ------+--------+-------------+-------------+-----------+-------------------------------------------------+----------------
    #  MCL1 |     -1 | NM_182763.2 |         208 |      1024 | myeloid cell leukemia sequence 1 (BCL2-related) | This gene encod
    # 
    # reece=> select * from uta.tx_exons where ac='NM_182763.2';
    #      ac      | ord | name | t_start_i | t_end_i |    ref     | g_start_i |  g_end_i  |    cigar     | 
    # -------------+-----+------+-----------+---------+------------+-----------+-----------+--------------+---------------------
    #  NM_182763.2 |   1 | 1b   |         0 |     896 | GRCh37.p10 | 150551318 | 150552214 | 896M         |
    #  NM_182763.2 |   2 | 3    |       896 |    3841 | GRCh37.p10 | 150547026 | 150549967 | 1077M4I1864M | GATGGGTTTGTGGAGTTCTT
    def test_transcriptmapper_TranscriptMapper_2_MCL1(self):
        ac = 'NM_182763.2'
        tm = TranscriptMapper(self.db,ac,self.ref)

        # exon 1, 1nt at either end
        self.assertEqual( tm.g_to_r(150552213,150552214), (0,1) )
        self.assertEqual( tm.g_to_r(150551318,150551319), (895,896) )
        self.assertEqual( tm.r_to_g(0,1), (150552213,150552214) )
        self.assertEqual( tm.r_to_g(895,896), (150551318,150551319) )

        # exon 2, 1nt at either end
        self.assertEqual( tm.g_to_r(150549966,150549967), (896,897) )
        self.assertEqual( tm.g_to_r(150547026,150547027), (3840,3841) )
        self.assertEqual( tm.r_to_g(896,897), (150549966,150549967) )
        self.assertEqual( tm.r_to_g(3840,3841), (150547026,150547027) )
        
        # exon 2, 4nt insertion ~ r.2760
        # See http://tinyurl.com/mwegybw
        # The coords of this indel via NW alignment differ from those at
        # NCBI, but are the same canonicalized variant.  Nothing to do
        # about that short of running Splign ourselves.
        self.assertEqual( tm.r_to_g(1972, 1972), (150548891, 150548891) )
        self.assertEqual( tm.r_to_g(1972, 1973), (150548890, 150548891) )
        self.assertEqual( tm.r_to_g(1972, 1974), (150548890, 150548891) )
        self.assertEqual( tm.r_to_g(1972, 1975), (150548890, 150548891) )
        self.assertEqual( tm.r_to_g(1972, 1976), (150548890, 150548891) )
        self.assertEqual( tm.r_to_g(1972, 1977), (150548890, 150548891) )
        self.assertEqual( tm.r_to_g(1972, 1978), (150548889, 150548891) )

        self.assertEqual( tm.g_to_r(150548891, 150548891), (1972, 1972) )
        self.assertEqual( tm.g_to_r(150548890, 150548891), (1972, 1973) )
        self.assertEqual( tm.g_to_r(150548889, 150548891), (1972, 1978) )

        # around cds_start (208) and cds_end (1024), mindful of *non-coding* ins (4I)
        # i.e., we *don't* need to account for the 4nt insertion here
        self.assertEquals( tm.r_to_c(208, 1024), (0,1024-208) )
        self.assertEquals( tm.c_to_r(0,1024-208), (208, 1024) )
        self.assertEquals( tm.g_to_c(150552214-208,150552214-208), (0,0) )
        self.assertEquals( tm.c_to_g(0,0), (150552214-208,150552214-208) )
        # cds_end is in 2nd exon
        self.assertEquals( tm.g_to_c(150549967-(1024-896),150549967-(1024-896)), (1024-208,1024-208) )
        self.assertEquals( tm.c_to_g(1024-208,1024-208), (150549967-(1024-896),150549967-(1024-896)) )

        
    # reece=> select * from uta.tx_info where ac = 'NM_145171.3';
    #  gene  | strand |     ac      | cds_start_i | cds_end_i |            descr            | summary  
    # -------+--------+-------------+-------------+-----------+-----------------------------+-----------------------------------
    #  GPHB5 |     -1 | NM_145171.3 |          57 |       450 | glycoprotein hormone beta 5 | GPHB5 is a cystine knot-forming...
    # 
    # reece=> select * from uta.tx_exons where ac = 'NM_145171.3' order by g_start_i;
    #      ac      | ord | name | t_start_i | t_end_i |    ref     | g_start_i | g_end_i  |   cigar   | g_seq_a
    # -------------+-----+------+-----------+---------+------------+-----------+----------+-----------+-------------------------
    #  NM_145171.3 |   3 | 3    |       261 |     543 | GRCh37.p10 |  63779548 | 63779830 | 282M      |                         
    #  NM_145171.3 |   2 | 2    |        56 |     261 | GRCh37.p10 |  63784360 | 63784564 | 156M1I48M | CATGAAGCTGGCATTCCTCTT...
    #  NM_145171.3 |   1 | 1    |         0 |      56 | GRCh37.p10 |  63785537 | 63785593 | 56M       |
    # def test_transcriptmapper_TranscriptMapper_GPHB5(self):
    #     ac = 'NM_145171.3'
    #     tm = TranscriptMapper(self.db,ac,self.ref)
    #     pass



if __name__ == '__main__':
    unittest.main()
