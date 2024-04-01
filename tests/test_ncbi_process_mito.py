import os
import unittest
from unittest.mock import MagicMock, patch

from Bio.SeqRecord import SeqRecord

from sbin.ncbi_process_mito import (
    download_mito_files,
    get_mito_genes,
    parse_db_xrefs,
    parse_nomenclature_value,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class TestNcbiProcessMito(unittest.TestCase):
    def verify_mito_gene_attributes(self, mito_gene, expected_values):
        for k, v in expected_values.items():
            try:
                self.assertEqual(getattr(mito_gene, k), v)
            except AssertionError:
                print(
                    f"Test failure on mito gene {mito_gene.gene_symbol} ({mito_gene.gene_id}) "
                    f'attribute "{k}" with value "{v}" not equal to "{getattr(mito_gene, k)}"'
                )
                raise

    @patch("sbin.ncbi_process_mito.download_from_eutils")
    def test_download_mito_files(self, mock_download):
        output_dir = "test_dir"
        accession = "test_accession"
        result = download_mito_files(output_dir, accession)
        self.assertEqual(
            result,
            {
                "gbff": "test_dir/test_accession.gbff",
                "fna": "test_dir/test_accession.fna",
            },
        )
        mock_download.assert_any_call(accession, "gb", f"{output_dir}/{accession}.gbff")
        mock_download.assert_any_call(
            accession, "fasta", f"{output_dir}/{accession}.fna"
        )

    def test_db_xrefs(self):
        gb_feature_mock = MagicMock(spec=SeqRecord)
        gb_feature_mock.qualifiers = {
            "db_xref": ["GeneID:4558", "HGNC:HGNC:7481", "MIM:590070"]
        }

        result = parse_db_xrefs(gb_feature_mock)
        self.assertEqual(
            result, {"GeneID": "4558", "HGNC": "HGNC:7481", "MIM": "590070"}
        )

    def test_db_xrefs_empty(self):
        gb_feature_mock = MagicMock(spec=SeqRecord)
        gb_feature_mock.qualifiers = {}

        result = parse_db_xrefs(gb_feature_mock)
        self.assertEqual(result, {})

    def test_parse_nomenclature_value(self):
        gb_feature_mock = MagicMock(spec=SeqRecord)
        gb_feature_mock.qualifiers = {
            "nomenclature": [
                "Official Symbol: MT-TF | Name: mitochondrially encoded tRNA phenylalanine | Provided by: HGNC:HGNC:7481"
            ]
        }

        result = parse_nomenclature_value(gb_feature_mock)
        self.assertEqual(
            result,
            {
                "Official Symbol": "MT-TF",
                "Name": "mitochondrially encoded tRNA phenylalanine",
                "Provided by": "HGNC:HGNC:7481",
            },
        )

    def test_parse_nomenclature_value_empty(self):
        gb_feature_mock = MagicMock(spec=SeqRecord)
        gb_feature_mock.qualifiers = {}

        result = parse_nomenclature_value(gb_feature_mock)
        self.assertEqual(result, {})

    def test_get_mito_genes(self):
        mito_genbank_filepath = f"{BASE_DIR}/data/NC_012920.1.gbff"
        results = [_ for _ in get_mito_genes(mito_genbank_filepath)]
        expected_gene_ids = [
            4508,
            4509,
            4511,
            4512,
            4513,
            4514,
            4519,
            4535,
            4536,
            4537,
            4538,
            4539,
            4540,
            4541,
            4549,
            4550,
            4553,
            4555,
            4556,
            4558,
            4563,
            4564,
            4565,
            4566,
            4567,
            4568,
            4569,
            4570,
            4571,
            4572,
            4573,
            4574,
            4575,
            4576,
            4577,
            4578,
            4579,
        ]
        expected_gene_symbols = [
            "MT-ATP6",
            "MT-ATP8",
            "MT-CO1",
            "MT-CO2",
            "MT-CO3",
            "MT-CYB",
            "MT-ND1",
            "MT-ND2",
            "MT-ND3",
            "MT-ND4",
            "MT-ND4L",
            "MT-ND5",
            "MT-ND6",
            "MT-RNR1",
            "MT-RNR2",
            "MT-TA",
            "MT-TC",
            "MT-TD",
            "MT-TE",
            "MT-TF",
            "MT-TG",
            "MT-TH",
            "MT-TI",
            "MT-TK",
            "MT-TL1",
            "MT-TL2",
            "MT-TM",
            "MT-TN",
            "MT-TP",
            "MT-TQ",
            "MT-TR",
            "MT-TS1",
            "MT-TS2",
            "MT-TT",
            "MT-TV",
            "MT-TW",
            "MT-TY",
        ]
        expected_origin = "NCBI"
        expected_aln_method = "splign"

        self.assertEqual(len(results), 37)
        self.assertEqual(sorted([r.gene_id for r in results]), expected_gene_ids)
        self.assertEqual(
            sorted([r.gene_symbol for r in results]), expected_gene_symbols
        )
        self.assertEqual([r.origin for r in results], [expected_origin] * 37)
        self.assertEqual(
            [r.alignment_method for r in results], [expected_aln_method] * 37
        )

        results_by_gene = {mg.gene_id: mg for mg in results}

        # Expected results for "MT-TV" non-coding tRNA gene on the plus strand
        expected_mg4577_values = {
            "gene_symbol": "MT-TV",
            "name": "mitochondrially encoded tRNA valine",
            "tx_ac": "NC_012920.1_01601_01670",
            "tx_seq": "CAGAGTGTAGCTTAACACAAAGCACCCAACTTACACTTAGGAGATTTCAACTTAACTTGACCGCTCTGA",
            "tx_start": 0,
            "tx_end": 69,
            "alt_ac": "NC_012920.1",
            "alt_start": 1601,
            "alt_end": 1670,
            "strand": "+",
            "transl_table": None,
            "transl_except": None,
            "pro_ac": None,
            "pro_seq": None,
        }
        self.verify_mito_gene_attributes(results_by_gene[4577], expected_mg4577_values)

        # Expected results for "MT-TQ" tRNA gene on the minus strand
        expected_mg4572_values = {
            "gene_symbol": "MT-TQ",
            "name": "mitochondrially encoded tRNA glutamine",
            "tx_ac": "NC_012920.1_04328_04400",
            "tx_seq": "TAGGATGGGGTGTGATAGGTGGCACGGAGAATTTTGGATTCTCAGGGATGGGTTCGATTCTCATAGTCCTAG",
            "tx_start": 0,
            "tx_end": 72,
            "alt_ac": "NC_012920.1",
            "alt_start": 4328,
            "alt_end": 4400,
            "strand": "-",
            "transl_table": None,
            "transl_except": None,
            "pro_ac": None,
            "pro_seq": None,
        }
        self.verify_mito_gene_attributes(results_by_gene[4572], expected_mg4572_values)

        # Expected results for "MT-CO2" coding gene on the plus strand
        expected_mg4513_values = {
            "gene_symbol": "MT-CO2",
            "name": "mitochondrially encoded cytochrome c oxidase II",
            "tx_ac": "NC_012920.1_07585_08269",
            "tx_seq": "ATGGCACATGCAGCGCAAGTAGGTCTACAAGACGCTACTTCCCCTATCATAGAAGAGCTTATCACCTTTCATGATCACGCCCTCATAATCATTT"
            "TCCTTATCTGCTTCCTAGTCCTGTATGCCCTTTTCCTAACACTCACAACAAAACTAACTAATACTAACATCTCAGACGCTCAGGAAATAGAAACCGTCTGAACT"
            "ATCCTGCCCGCCATCATCCTAGTCCTCATCGCCCTCCCATCCCTACGCATCCTTTACATAACAGACGAGGTCAACGATCCCTCCCTTACCATCAAATCAATTGG"
            "CCACCAATGGTACTGAACCTACGAGTACACCGACTACGGCGGACTAATCTTCAACTCCTACATACTTCCCCCATTATTCCTAGAACCAGGCGACCTGCGACTCC"
            "TTGACGTTGACAATCGAGTAGTACTCCCGATTGAAGCCCCCATTCGTATAATAATTACATCACAAGACGTCTTGCACTCATGAGCTGTCCCCACATTAGGCTTA"
            "AAAACAGATGCAATTCCCGGACGTCTAAACCAAACCACTTTCACCGCTACACGACCGGGGGTATACTACGGTCAATGCTCTGAAATCTGTGGAGCAAACCACAG"
            "TTTCATGCCCATCGTCCTAGAATTAATTCCCCTAAAAATCTTTGAAATAGGGCCCGTATTTACCCTATAG",
            "tx_start": 0,
            "tx_end": 684,
            "alt_ac": "NC_012920.1",
            "alt_start": 7585,
            "alt_end": 8269,
            "strand": "+",
            "transl_table": "2",
            "transl_except": None,
            "pro_ac": "YP_003024029.1",
            "pro_seq": "MAHAAQVGLQDATSPIMEELITFHDHALMIIFLICFLVLYALFLTLTTKLTNTNISDAQEMETVWTILPAIILVLIALPSLRILYMTDEVNDP"
            "SLTIKSIGHQWYWTYEYTDYGGLIFNSYMLPPLFLEPGDLRLLDVDNRVVLPIEAPIRMMITSQDVLHSWAVPTLGLKTDAIPGRLNQTTFTATRPGVYYGQCS"
            "EICGANHSFMPIVLELIPLKIFEMGPVFTL",
        }
        self.verify_mito_gene_attributes(results_by_gene[4513], expected_mg4513_values)

        # Expected results for "MT-ND1" coding gene on the minus strand with a transl_except
        expected_mg4535_values = {
            "gene_symbol": "MT-ND1",
            "name": "mitochondrially encoded NADH dehydrogenase 1",
            "tx_ac": "NC_012920.1_03306_04262",
            "tx_seq": "ATACCCATGGCCAACCTCCTACTCCTCATTGTACCCATTCTAATCGCAATGGCATTCCTAATGCTTACCGAACGAAAAATTCTAGGCTATATAC"
            "AACTACGCAAAGGCCCCAACGTTGTAGGCCCCTACGGGCTACTACAACCCTTCGCTGACGCCATAAAACTCTTCACCAAAGAGCCCCTAAAACCCGCCACATCT"
            "ACCATCACCCTCTACATCACCGCCCCGACCTTAGCTCTCACCATCGCTCTTCTACTATGAACCCCCCTCCCCATACCCAACCCCCTGGTCAACCTCAACCTAGG"
            "CCTCCTATTTATTCTAGCCACCTCTAGCCTAGCCGTTTACTCAATCCTCTGATCAGGGTGAGCATCAAACTCAAACTACGCCCTGATCGGCGCACTGCGAGCAG"
            "TAGCCCAAACAATCTCATATGAAGTCACCCTAGCCATCATTCTACTATCAACATTACTAATAAGTGGCTCCTTTAACCTCTCCACCCTTATCACAACACAAGAA"
            "CACCTCTGATTACTCCTGCCATCATGACCCTTGGCCATAATATGATTTATCTCCACACTAGCAGAGACCAACCGAACCCCCTTCGACCTTGCCGAAGGGGAGTC"
            "CGAACTAGTCTCAGGCTTCAACATCGAATACGCCGCAGGCCCCTTCGCCCTATTCTTCATAGCCGAATACACAAACATTATTATAATAAACACCCTCACCACTA"
            "CAATCTTCCTAGGAACAACATATGACGCACTCTCCCCTGAACTCTACACAACATATTTTGTCACCAAGACCCTACTTCTAACCTCCCTGTTCTTATGAATTCGA"
            "ACAGCATACCCCCGATTCCGCTACGACCAACTCATACACCTCCTATGAAAAAACTTCCTACCACTCACCCTAGCATTACTTATATGATATGTCTCCATACCCAT"
            "TACAATCTCCAGCATTCCCCCTCAAACCTA",
            "tx_start": 0,
            "tx_end": 956,
            "alt_ac": "NC_012920.1",
            "alt_start": 3306,
            "alt_end": 4262,
            "strand": "+",
            "transl_table": "2",
            "transl_except": "(pos:4261..4262,aa:TERM)",
            "pro_ac": "YP_003024026.1",
            "pro_seq": "MPMANLLLLIVPILIAMAFLMLTERKILGYMQLRKGPNVVGPYGLLQPFADAMKLFTKEPLKPATSTITLYITAPTLALTIALLLWTPLPMPN"
            "PLVNLNLGLLFILATSSLAVYSILWSGWASNSNYALIGALRAVAQTISYEVTLAIILLSTLLMSGSFNLSTLITTQEHLWLLLPSWPLAMMWFISTLAETNRTP"
            "FDLAEGESELVSGFNIEYAAGPFALFFMAEYTNIIMMNTLTTTIFLGTTYDALSPELYTTYFVTKTLLLTSLFLWIRTAYPRFRYDQLMHLLWKNFLPLTLALL"
            "MWYVSMPITISSIPPQT",
        }
        self.verify_mito_gene_attributes(results_by_gene[4535], expected_mg4535_values)
