import unittest
from uta.formats.txinfo import TxInfo


class TestUtaFormats(unittest.TestCase):

    def test_txinfo_serialize_transl_except(self):
        self.assertIsNone(TxInfo.serialize_transl_except(None))
        self.assertEqual(TxInfo.serialize_transl_except([]), '')
        self.assertEqual(TxInfo.serialize_transl_except(['(pos:333..335,aa:Sec)', '(pos:1017,aa:TERM)']), '(pos:333..335,aa:Sec);(pos:1017,aa:TERM)')
