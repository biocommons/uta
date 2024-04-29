import os
import unittest
from unittest.mock import Mock, PropertyMock, patch

from Bio import SeqIO
from parameterized import param, parameterized

from uta.parsers.seqrecord import SeqRecordFacade, SeqRecordFeatureError


class TestSeqRecordFacade(unittest.TestCase):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

    @parameterized.expand([
        param(
            'NM_001396027 - single exon feature',
            file_name='rna.NM_001396027.gbff',
            expected_id='NM_001396027.1',
            expected_gene_symbol='FAM246C',
            expected_gene_id='117134596',
            expected_cds_se_i=(0, 696),
            expected_exons_se_i=[(0, 696)],
        ),
        param(
            'NM_001396027 - multiple exon features',
            file_name='rna.NM_001996.gbff',
            expected_id='NM_001996.4',
            expected_gene_symbol='FBLN1',
            expected_gene_id='2192',
            expected_cds_se_i=(103, 2155),
            expected_exons_se_i=[
                (0, 182),
                (182, 288),
                (288, 424),
                (424, 587),
                (587, 647),
                (647, 749),
                (749, 887),
                (887, 1025),
                (1025, 1169),
                (1169, 1298),
                (1298, 1424),
                (1424, 1544),
                (1544, 1676),
                (1676, 1800),
                (1800, 2251),
            ],
        ),
        param(
            'NR_173080 - no exon features, ncRNA',
            file_name='rna.NR_173080.gbff',
            expected_id='NR_173080.1',
            expected_gene_symbol='LOC122455341',
            expected_gene_id='122455341',
            expected_cds_se_i=None,
            expected_exons_se_i=[(0,1073)],
        ),
        param(
            'NR_173148 - no exon features, misc_RNA',
            file_name='rna.NR_173148.gbff',
            expected_id='NR_173148.1',
            expected_gene_symbol='FAM246C',
            expected_gene_id='117134596',
            expected_cds_se_i=None,
            expected_exons_se_i=[(0,698)],
        ),
    ])
    def test_seq_record_facade(
        self,
        test_name,
        file_name,
        expected_id,
        expected_gene_symbol,
        expected_gene_id,
        expected_cds_se_i,
        expected_exons_se_i,
    ):
        gbff_file = os.path.join(self.test_data_dir, file_name)
        seq_record = [sr for sr in SeqIO.parse(gbff_file, 'gb')][0]
        self.seq_record_facade = SeqRecordFacade(seq_record)
        assert self.seq_record_facade.id == expected_id
        assert self.seq_record_facade.gene_symbol == expected_gene_symbol
        assert self.seq_record_facade.gene_id == expected_gene_id
        assert self.seq_record_facade.cds_se_i == expected_cds_se_i
        assert self.seq_record_facade.exons_se_i == expected_exons_se_i

    @parameterized.expand([
        param('no genes', features={}),
        param('no genes', features={'gene': []}),
        param('more than one gene', features={'gene': [Mock(), Mock()]}),
        param('more than one CDS', features={'CDS': [Mock(), Mock()]}),
    ])
    def test_validate_features_by_type_invalid(self, test_name, features):
        with self.assertRaises(SeqRecordFeatureError):
            SeqRecordFacade.validate_features_by_type(features)

    def test_cds_feature(self):
        with patch('uta.parsers.seqrecord.SeqRecordFacade.features_by_type', new_callable=PropertyMock) as mock_features_by_type:
            # no CDS feature
            mock_features_by_type.return_value = {}
            srf = SeqRecordFacade(seqrecord=Mock())
            self.assertIsNone(srf.cds_feature)
            # one CDS feature
            dummy_cds_feature = Mock()
            mock_features_by_type.return_value = {'CDS': [dummy_cds_feature]}
            srf = SeqRecordFacade(seqrecord=Mock())
            self.assertIs(srf.cds_feature, dummy_cds_feature)

    def test_transl_except(self):
        with patch('uta.parsers.seqrecord.SeqRecordFacade.cds_feature', new_callable=PropertyMock) as mock_cds_feature:
            # no CDS feature
            mock_cds_feature.return_value = None
            srf = SeqRecordFacade(seqrecord=Mock())
            self.assertIsNone(srf.transl_except)

            # one CDS feature without transl_except
            mock_cds_feature.return_value = Mock(qualifiers={})
            srf = SeqRecordFacade(seqrecord=Mock())
            self.assertIsNone(srf.transl_except)

            # one CDS feature with transl_except
            mock_cds_feature.return_value = Mock(qualifiers={'transl_except': ['(pos:333..335,aa:Sec)', '(pos:1017,aa:TERM)']})
            srf = SeqRecordFacade(seqrecord=Mock())
            self.assertEqual(srf.transl_except, ['(pos:333..335,aa:Sec)', '(pos:1017,aa:TERM)'])


if __name__ == '__main__':
    unittest.main()
