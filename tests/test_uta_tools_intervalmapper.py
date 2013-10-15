import unittest

from uta.exceptions import *
from uta.tools.intervalmapper import Interval, IntervalPair, IntervalMapper

class Test_intervalmapper_interval(unittest.TestCase):
    def test_intervalmapper_interval(self):
        iv = Interval(23,45)
        self.assertEqual( (iv.start_i, iv.end_i) , (23,45) )
        with self.assertRaises(InvalidIntervalError):
            iv = Interval(45,23)

class Test_intervalmapper_intervalpair(unittest.TestCase):
    def test_intervalmapper_intervalpair(self):
        i = IntervalPair(Interval(12,34), Interval(56,78))
        self.assertEqual( (i.ref.start_i,i.ref.end_i), (12,34) )
        self.assertEqual( (i.tgt.start_i,i.tgt.end_i), (56,78) )
        with self.assertRaises(InvalidIntervalError):
            ip = IntervalPair(Interval(12,34),Interval(12,33))


class Test_intervalmapper_intervalmapper_1(unittest.TestCase):
    """Tests mappings on the following alignment:
        0         15   20         35         50
        |==========|====|==========|==========|
        |          |   /          /|          |
        |          |  /          / |          |
        |          | /          /  |          |
        |          |/          /   |          |
        |==========|==========|====|==========|
        0         15         30   35         50
            15M   5D   15M      5I      15M  

  generated from:
  im = IntervalMapper.from_cigar('15M5D15M5I15M')
  im.interval_pairs
  [IntervalPair(ref=Interval(start_i=0,end_i=15),tgt=Interval(start_i=0,end_i=15)),
   IntervalPair(ref=Interval(start_i=15,end_i=20),tgt=Interval(start_i=15,end_i=15)),
   IntervalPair(ref=Interval(start_i=20,end_i=35),tgt=Interval(start_i=15,end_i=30)),
   IntervalPair(ref=Interval(start_i=35,end_i=35),tgt=Interval(start_i=30,end_i=35)),
   IntervalPair(ref=Interval(start_i=35,end_i=50),tgt=Interval(start_i=35,end_i=50))]
   """
    def setUp(self):
        self.im = IntervalMapper.from_cigar('15M5D15M5I15M')

    def Test_intervalmapper_simple(self):
        #"""tests that are reciprocal and don't involve min/max extent concerns around indels"""
        for refc,tgtc in [ 
                ((0,0), (0,0)),
                ((5,10), (5,10)),
                ((21,22), (16,17)),
                ((40,45), (40,45)),
                ((5,45), (5,45)),
                ]:
            self.assertEqual( self.im.map_ref_to_tgt(*refc), tgtc )
            self.assertEqual( self.im.map_tgt_to_ref(*tgtc), refc )


    def Test_intervalmapper_complex_forward(self):
        for refc,tgtc_min,tgtc_max in [
                ((14,21), (14,16), (14,16)),
                ((14,16), (14,15), (14,15)),
                ((19,21), (15,16), (15,16)),
                ((16,18), (15,15), (15,15)),
                ((34,36), (29,36), (29,36)),
                ((35,35), (30,35), (30,35)),
                ((34,35), (29,30), (29,35)),
                ((35,36), (35,36), (30,36)),
                ]:
            self.assertEqual( self.im.map_ref_to_tgt(*refc, max_extent=False), tgtc_min )
            self.assertEqual( self.im.map_ref_to_tgt(*refc, max_extent=True) , tgtc_max )


#    def Test_intervalmapper_exceptions(self):
#        self.assertRaises(InvalidIntervalError, lambda: self.im.map_ref_to_tgt(50,51))
#        self.assertRaises(InvalidIntervalError, lambda: self.im.map_tgt_to_ref(50,51))

if __name__ == '__main__':
    unittest.main()



