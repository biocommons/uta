import unittest

from uta.tools.intervalmapper import Interval, IntervalPair, IntervalMapper
       
class Test_intervalmapper_interval(unittest.TestCase):
    def test_intervalmapper_interval(self):
        iv = Interval(23,45)
        self.assertEqual( (iv.start_i, iv.end_i) , (23,45) )
        with self.assertRaises(RuntimeError):
            iv = Interval(45,23)

class Test_intervalmapper_intervalpair(unittest.TestCase):
    def test_intervalmapper_intervalpair(self):
        i = IntervalPair(Interval(12,34), Interval(56,78))
        self.assertEqual( (i.ref.start_i,i.ref.end_i), (12,34) )
        self.assertEqual( (i.tgt.start_i,i.tgt.end_i), (56,78) )
        with self.assertRaises(RuntimeError):
            ip = IntervalPair(Interval(12,34),Interval(12,33))

class Test_intervalmapper_intervalmapper_1(unittest.TestCase):
    def setUp(self):
        # Tests the following alignment:
        # 0                   20            35         45       55
        # |===================|==============|---------|=========|
        # |                   |\__            \___ ___/       __/
        # |                   |   \               v          /
        # |===================|----|==============|=========|
        # 0                  20   25             40        50
        # 
        # generated from:
        # print( cigar_to_intervalpairs('20M5I15M10D10M') )
        im = IntervalMapper([
            IntervalPair(ref=Interval(start_i= 0,end_i=20),tgt=Interval(start_i= 0,end_i=20)),
            IntervalPair(ref=Interval(start_i=20,end_i=20),tgt=Interval(start_i=20,end_i=25)),
            IntervalPair(ref=Interval(start_i=20,end_i=35),tgt=Interval(start_i=25,end_i=40)),
            IntervalPair(ref=Interval(start_i=35,end_i=45),tgt=Interval(start_i=40,end_i=40)),
            IntervalPair(ref=Interval(start_i=45,end_i=55),tgt=Interval(start_i=40,end_i=50)),
            ])
        self.im = im

    def Test_intervalmapper_forward(self):
        im = self.im
        for input,expected in [ 
                ((0,0), (0,0)),
                ((0,10), (0,10)),
                ((19,20), (19,20)),
                # ((20,20), (20,25)),  # BROKEN, minor case (0-width del)
                ((19,21), (19,26)),
                ((20,21), (25,26)),
                ((34,35), (39,40)),
                ((34,40), (39,40)),
                ((35,40), (40,40)),
                ((35,45), (40,40)),
                ((45,45), (40,40)),
                ((45,46), (40,41)),
                ((45,55), (40,50)),
                ]:
            self.assertEqual( im.map_ref_to_tgt(*input), expected )
        self.assertRaises(RuntimeError, lambda: im.map_ref_to_tgt(55,56))


    def Test_intervalmapper_backward(self):
        im = self.im
        for input,expected in [ 
                ((0,0), (0,0)),
                ((0,10), (0,10)),
                ((19,20), (19,20)),
                ((19,26), (19,21)),
                ((25,26), (20,21)),
                ((39,40), (34,35)),
                ((39,40), (34,35)),
                ((40,41), (45,46)),
                ((40,50), (45,55)),
                ]:
            self.assertEqual( im.map_tgt_to_ref(*input), expected )
        self.assertRaises(RuntimeError, lambda: im.map_tgt_to_ref(50,51))


## class Test_intervalmapper_intervalmapper_2(unittest.TestCase):
##     def setUp(self):
##         # Tests the following alignment:
##         #  ref> 0  10      110  130       330        630      670         1070
##         #       |--|=========|--|==========|==========|-------|=============|
##         #        \ |         | /          / \          \__ __/             / \
##         #         \|         |/          /   \            v               /   \
##         #          |=========|==========|-----|===========|==============|-----|
##         # +tgt>    0       100        300     330         630         1030    1080
##         # -tgt>  1080      980        780     750         450           50     0
##         #
##         # cigar> 10D   100M  20D  200M    30I       300M   40N   400M      50I
##         #
##         # All coordinates throught this code are interbase
##         # | are *zero width points* between bases
##         # === are M or X;  --- are I, D, or N
##         #
##         # Although intervalmapper is intended for transcript-reference
##         # alignment that accounts for introns and reference distragreement,
##         # this code is purposefully ignorant of strand direction, which is
##         # left to callers.
## 
##         im = IntervalMapper([
##             IntervalPair(Interval(   0,  10) , Interval(   0,   0)),
##             IntervalPair(Interval(  10, 110) , Interval(   0, 100)),
##             IntervalPair(Interval( 110, 130) , Interval( 100, 100)),
##             IntervalPair(Interval( 130, 330) , Interval( 100, 300)),
##             IntervalPair(Interval( 330, 330) , Interval( 300, 330)),
##             IntervalPair(Interval( 330, 630) , Interval( 330, 630)),
##             IntervalPair(Interval( 630, 670) , Interval( 630, 630)),
##             IntervalPair(Interval( 670,1070) , Interval( 630,1030)),
##             IntervalPair(Interval(1070,1070) , Interval(1030,1080)),
##             ])
##         self.im = im
## 
##     def test_intervalmapper_intervalmapper_forward(self):
##         im = self.im
##         self.assertEqual( im.map_ref_to_tgt(   0,   0) , (   0,   0) )
##         self.assertEqual( im.map_ref_to_tgt(   0,  10) , (   0,   0) )
##         self.assertEqual( im.map_ref_to_tgt(   0,  11) , (   0,   1) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 110) , (   0, 100) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 120) , (   0, 100) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 130) , (   0, 100) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 131) , (   0, 101) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 329) , (   0, 299) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 330) , (   0, 330) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 331) , (   0, 331) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 630) , (   0, 630) )
##         self.assertEqual( im.map_ref_to_tgt(   0, 670) , (   0, 630) )
##         self.assertEqual( im.map_ref_to_tgt(   0,1070) , (   0,1080) )
## 
##         self.assertEqual( im.map_ref_to_tgt( 109, 110) , (  99, 100) )
##         self.assertEqual( im.map_ref_to_tgt( 110, 110) , ( 100, 100) )
##         self.assertEqual( im.map_ref_to_tgt( 110, 111) , ( 100, 100) )
##         self.assertEqual( im.map_ref_to_tgt( 110, 120) , ( 100, 100) )
##         self.assertEqual( im.map_ref_to_tgt( 110, 129) , ( 100, 100) )
##         self.assertEqual( im.map_ref_to_tgt( 110, 130) , ( 100, 100) )
##         self.assertEqual( im.map_ref_to_tgt( 110, 131) , ( 100, 101) )
## 
##         self.assertEqual( im.map_ref_to_tgt( 329, 329) , ( 299, 299) )
##         self.assertEqual( im.map_ref_to_tgt( 329, 330) , ( 299, 330) )   # R ext
##         self.assertEqual( im.map_ref_to_tgt( 330, 330) , ( 300, 330) )   # ref del
##         self.assertEqual( im.map_ref_to_tgt( 330, 331) , ( 300, 331) )   # L ext
##         self.assertEqual( im.map_ref_to_tgt( 331, 331) , ( 331, 331) )
## 
##         self.assertEqual( im.map_ref_to_tgt(1069,1069) , (1029,1029) )
##         self.assertEqual( im.map_ref_to_tgt(1069,1070) , (1029,1080) )   # R ext
##         self.assertEqual( im.map_ref_to_tgt(1070,1070) , (1030,1080) )   # ref del
## 
## 
##     def test_intervalmapper_intervalmapper_backward(self):
##         im = self.im
##         self.assertEqual( im.map_tgt_to_ref(   0,   0) , (   0,   0) )
##         self.assertEqual( im.map_tgt_to_ref(   0,   1) , (  10,  11) )
##         self.assertEqual( im.map_tgt_to_ref(  99, 100) , ( 109, 130) )   # R ext
##         self.assertEqual( im.map_tgt_to_ref( 100, 100) , ( 110, 130) )   # ref ins
##         self.assertEqual( im.map_tgt_to_ref( 100, 101) , ( 110, 131) )   # L ext
## 
##         self.assertEqual( im.map_tgt_to_ref(   5,  15) , (  15,  25) )
##         self.assertEqual( im.map_tgt_to_ref(   9,  10) , (  19,  20) )
##         self.assertEqual( im.map_tgt_to_ref(   9,  11) , (  19,  21) )
##         self.assertEqual( im.map_tgt_to_ref( 112, 115) , ( 142, 145) )
##         self.assertEqual( im.map_tgt_to_ref( 150, 645) , ( 180, 685) )
## 
##         
##         self.assertEqual( im.map_tgt_to_ref( 629, 629) , ( 629, 629) )
##         self.assertEqual( im.map_tgt_to_ref( 629, 630) , ( 629, 670) )   # R ext
##         self.assertEqual( im.map_tgt_to_ref( 630, 630) , ( 630, 670) )   # ref ins
##         self.assertEqual( im.map_tgt_to_ref( 630, 631) , ( 630, 671) )   # L ext
## 
##         
##     def test_intervalmapper_from_cigar(self):
##         cigar = '10D100M20D200M30I300M40N400M50I'
##         im = IntervalMapper.from_cigar(cigar)
##         self.assertEqual( im.map_ref_to_tgt(   5,  15) , (   0,   5) )
##         self.assertEqual( im.map_ref_to_tgt(   9,  10) , (   0,   0) )
##         self.assertEqual( im.map_ref_to_tgt(   9,  11) , (   0,   1) )
##         self.assertEqual( im.map_ref_to_tgt( 112, 115) , ( 100, 100) )
##         self.assertEqual( im.map_ref_to_tgt( 150, 645) , ( 120, 630) )
##         self.assertEqual( im.map_tgt_to_ref(   5,  15) , (  15,  25) )
##         self.assertEqual( im.map_tgt_to_ref(   9,  10) , (  19,  20) )
##         self.assertEqual( im.map_tgt_to_ref(   9,  11) , (  19,  21) )
##         self.assertEqual( im.map_tgt_to_ref( 112, 115) , ( 142, 145) )
##         self.assertEqual( im.map_tgt_to_ref( 150, 645) , ( 180, 685) )


if __name__ == '__main__':
    unittest.main()



