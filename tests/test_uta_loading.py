import configparser
import signal
import unittest
from unittest.mock import Mock, patch

import sqlalchemy as sa
import testing.postgresql

import uta
import uta.loading as ul
import uta.models as usam


class TestUtaLoading(unittest.TestCase):

    def setUp(self):
        # setup test database
        self.db = testing.postgresql.Postgresql()
        self.session = uta.connect(self.db.url())

        admin_role = 'uta_admin'
        self.session.execute(sa.text(f'create user {admin_role}'))
        self.session.execute(sa.text(f'grant all privileges on database test to {admin_role}'))

        self.cf = configparser.ConfigParser()
        self.cf.add_section('uta')
        self.cf.set('uta', 'admin_role', 'uta_admin')

        ul.create_schema(self.session, {}, self.cf)
        ul.grant_permissions(self.session, {}, self.cf)

    def tearDown(self):
        self.session.close()
        self.db.stop(_signal=signal.SIGKILL)
        self.db.cleanup()

    def test_meta_data(self):
        """
        Metadata should exist, then updated when update_meta_data is called.
        """
        # the schema_version should match existing values in UTA models
        expected_schema_version = usam.schema_version
        md_schema_version = self.session.query(usam.Meta).filter(usam.Meta.key == 'schema_version').one()
        self.assertEqual(md_schema_version.value, expected_schema_version)

        new_schema_version = '9.9'
        with patch('uta.models.schema_version', new_schema_version):
            ul.update_meta_data(self.session, {}, self.cf)

        md_schema_version = self.session.query(usam.Meta).filter(usam.Meta.key == 'schema_version').one()
        self.assertEqual(md_schema_version.value, new_schema_version)

        md_updated_at = self.session.query(usam.Meta).filter(usam.Meta.key == 'updated on').one_or_none()
        self.assertIsNotNone(md_updated_at)

    def test_load_assoc_ac(self):
        """
        Loading file tests/data/assocacs.gz should create associated_accessions records in the database.
        Row will be created in associated_accessions even when transcript or origin does not exist in database.
        This is only the case until tx_ac and origin are converted to foreign keys.
        """

        # insert origins referenced in data file
        o1 = usam.Origin(
            name='NCBI',
            url='http://bogus.com/ncbi',
            url_ac_fmt='http://bogus.com/ncbi/{ac}',
        )
        self.session.add(o1)

        # insert genes required for transcripts
        g1 = usam.Gene(
            gene_id='49',
            hgnc='ACR',
            symbol='ACR',
            maploc='22q13.33',
            descr='acrosin',
            summary='acrosin',
            aliases='SPGF87',
            type='protein-coding',
            xrefs='MIM:102480,HGNC:HGNC:126,Ensembl:ENSG00000100312,AllianceGenome:HGNC:126',
        )
        g2 = usam.Gene(
            gene_id=50,
            hgnc='ACO2',
            symbol='ACO2',
            maploc='22q13.2',
            descr='aconitase 2',
            summary='aconitase 2',
            aliases='ACONM,HEL-S-284,ICRD,OCA8,OPA9',
            type='protein-coding',
            xrefs='MIM:100850,HGNC:HGNC:118,Ensembl:ENSG00000100412,AllianceGenome:HGNC:118',
        )
        self.session.add(g1)
        self.session.add(g2)

        # insert transcripts referenced in data file
        t1 = usam.Transcript(
            ac='NM_001097.3',
            origin=o1,
            gene_id=g1.gene_id,
            cds_start_i=0,
            cds_end_i=1,
            cds_md5='a',
        )
        t2 = usam.Transcript(
            ac='NM_001098.3',
            origin=o1,
            gene_id=g2.gene_id,
            cds_start_i=2,
            cds_end_i=3,
            cds_md5='b',
        )
        self.session.add(t1)
        self.session.add(t2)

        # pre-add one of the associated_acessions from the test data file
        # to demonstrate get-or-insert behavior
        p = usam.AssociatedAccessions(
            tx_ac='NM_001097.3',
            pro_ac='NP_001088.2',
            origin='NCBI',
        )
        self.session.add(p)

        self.session.commit()

        cf = configparser.ConfigParser()
        cf.add_section('uta')
        cf.set('uta', 'admin_role', 'uta_admin')

        ul.load_assoc_ac(self.session, {'FILE': 'tests/data/assocacs.gz'}, cf)

        # associated_accessions table should contain one record per line in file
        aa = self.session.query(usam.AssociatedAccessions).order_by(usam.AssociatedAccessions.tx_ac).all()
        aa_list = [{'tx_ac': aa.tx_ac, 'pro_ac': aa.pro_ac, 'origin_name': aa.origin} for aa in aa]
        expected_aa_list = [
            {
                'tx_ac': 'DummyTx',
                'pro_ac': 'DummyProtein',
                'origin_name': 'DummyOrigin',
            },
            {
                'tx_ac': 'NM_001097.3',
                'pro_ac': 'NP_001088.2',
                'origin_name': 'NCBI',
            },
            {
                'tx_ac': 'NM_001098.3',
                'pro_ac': 'NP_001089.1',
                'origin_name': 'NCBI',
            },
        ]
        self.assertEqual(aa_list, expected_aa_list)

    def test_load_txinfo(self):
        """
        Loading file tests/data/txinfo.gz should create transcript, exon_set, exon, and translation_exception records in the database.
        """

        # insert origins referenced in data file
        o1 = usam.Origin(
            name='NCBI',
            url='http://bogus.com/ncbi',
            url_ac_fmt='http://bogus.com/ncbi/{ac}',
        )
        self.session.add(o1)

        # insert genes required for transcripts
        g1 = usam.Gene(
            gene_id='140606',
            hgnc='SELENOM',
            symbol='SELENOM',
            maploc='22q12.2',
            descr='selenoprotein M',
            summary='selenoprotein M',
            aliases='SELM,SEPM',
            type='protein-coding',
            xrefs='MIM:610918,HGNC:HGNC:30397,Ensembl:ENSG00000198832,AllianceGenome:HGNC:30397',
        )
        g2 = usam.Gene(
            gene_id='4514',
            hgnc='MT-CO3',
            symbol='MT-CO3',
            maploc=None,
            descr='mitochondrially encoded cytochrome c oxidase III',
            summary='mitochondrially encoded cytochrome c oxidase III',
            aliases='COIII,MTCO3',
            type='protein-coding',
            xrefs='GeneID:4514,HGNC:HGNC:7422,MIM:516050',
        )
        self.session.add(g1)
        self.session.add(g2)
        self.session.commit()

        cf = configparser.ConfigParser()
        cf.add_section('uta')
        cf.set('uta', 'admin_role', 'uta_admin')

        with patch('uta.loading._get_seqfetcher', return_value=Mock(fetch=Mock(return_value='FAKESEQUENCE'))):
            ul.load_txinfo(self.session, {'FILE': 'tests/data/txinfo.gz'}, cf)

        transcript = self.session.query(usam.Transcript).filter(usam.Transcript.ac == 'NM_080430.4').one()
        self.assertEqual(
            {
                'ac': transcript.ac,
                'gene_id': transcript.gene_id,
                'cds_start_i': transcript.cds_start_i,
                'cds_end_i': transcript.cds_end_i,
                'codon_table': transcript.codon_table,
            },
            {
                'ac': 'NM_080430.4',
                'gene_id': '140606',
                'cds_start_i': 63,
                'cds_end_i': 501,
                'codon_table': '1',
            },
        )

        transcript = self.session.query(usam.Transcript).filter(usam.Transcript.ac == 'NC_012920.1_09206_09990').one()
        self.assertEqual(
            {
                'ac': transcript.ac,
                'gene_id': transcript.gene_id,
                'cds_start_i': transcript.cds_start_i,
                'cds_end_i': transcript.cds_end_i,
                'codon_table': transcript.codon_table,
            },
            {
                'ac': 'NC_012920.1_09206_09990',
                'gene_id': '4514',
                'cds_start_i': 0,
                'cds_end_i': 784,
                'codon_table': '2',
            },
        )

        exon_set = self.session.query(usam.ExonSet).filter(usam.ExonSet.tx_ac == 'NM_080430.4').one()
        exons = self.session.query(usam.Exon).filter(usam.Exon.exon_set_id == exon_set.exon_set_id).all()
        self.assertEqual(len(exons), 5)

        translation_exception = self.session.query(usam.TranslationException).filter(usam.TranslationException.tx_ac == 'NM_080430.4').one()
        self.assertEqual(
            {
                'tx_ac': translation_exception.tx_ac,
                'start_position': translation_exception.start_position,
                'end_position': translation_exception.end_position,
                'amino_acid': translation_exception.amino_acid,
            },
            {
                'tx_ac': 'NM_080430.4',
                'start_position': 204,
                'end_position': 207,
                'amino_acid': 'Sec',
            },
        )

    def test_load_exonset_with_exon_structure_mismatch(self):
        """
        Loading the test file tests/data/exonsets-mm-exons.gz should not raise an exception, exon alignments without
        a mismatch should load, those with a mismatch should be skipped and logged as such. The input file has
        alignments for 4 transcripts against NC_000001.11, but only 2 of them have the correct number of exons.
        We only expect the alignmets for NM_000911.4 and NM_001005277.1 to be loaded.
        """
        # setup
        # insert origins referenced in data file
        o1 = usam.Origin(
            name="NCBI",
            url="http://bogus.com/ncbi",
            url_ac_fmt="http://bogus.com/ncbi/{ac}",
        )
        self.session.add(o1)
        self.session.flush()

        for gene_data in [
            {
                "gene_id": "3352",
                "hgnc": "HTR1D",
                "symbol": "HTR1D",
                "type": "protein-coding",
            },
            {
                "gene_id": "4985",
                "hgnc": "OPRD1",
                "symbol": "OPRD1",
                "type": "protein-coding",
            },
            {
                "gene_id": "81399",
                "hgnc": "OR4F16",
                "symbol": "OR4F16",
                "type": "protein-coding",
            },
            {
                "gene_id": "79501",
                "hgnc": "OR4F5",
                "symbol": "OR4F5",
                "type": "protein-coding",
            },
        ]:
            gene = usam.Gene(**gene_data)
            self.session.add(gene)

        for tx_data in [
            {
                "ac": "NM_000864.5",
                "origin_id": o1.origin_id,
                "gene_id": "3352",
                "cds_start_i": 994,
                "cds_end_i": 2128,
                "cds_md5": "a",
            },
            {
                "ac": "NM_000911.4",
                "origin_id": o1.origin_id,
                "gene_id": "4985",
                "cds_start_i": 214,
                "cds_end_i": 1333,
                "cds_md5": "b",
            },
            {
                "ac": "NM_001005277.1",
                "origin_id": o1.origin_id,
                "gene_id": "81399",
                "cds_start_i": 0,
                "cds_end_i": 939,
                "cds_md5": "c",
            },
            {
                "ac": "NM_001005484.2",
                "origin_id": o1.origin_id,
                "gene_id": "79501",
                "cds_start_i": 60,
                "cds_end_i": 1041,
                "cds_md5": "d",
            },
        ]:
            tx = usam.Transcript(**tx_data)
            self.session.add(tx)
            es = usam.ExonSet(
                tx_ac=tx.ac,
                alt_ac=tx.ac,
                alt_strand=1,
                alt_aln_method="transcript",
            )
            self.session.add(es)
            self.session.flush()

        for exon_data in [
            ("NM_000864.5", 1, 0, 3319),  # exons for NM_000864.5 are 0,212;212,3319
            ("NM_000911.4", 1, 0, 441),
            ("NM_000911.4", 2, 441, 791),
            ("NM_000911.4", 3, 791, 9317),
            ("NM_001005277.1", 1, 0, 939),
            ("NM_001005484.2", 1, 0, 15),
            ("NM_001005484.2", 2, 15, 69),
            (
                "NM_001005484.2",
                3,
                69,
                1041,
            ),  # exons for NM_001005484.2 are 0,15;15,69;69,2618
            ("NM_001005484.2", 4, 1041, 2618),
        ]:
            es = (
                self.session.query(usam.ExonSet)
                .filter(
                    usam.ExonSet.tx_ac == exon_data[0], usam.ExonSet.alt_ac == exon_data[0]
                )
                .one()
            )
            exon = usam.Exon(
                exon_set_id=es.exon_set_id,
                start_i=exon_data[2],
                end_i=exon_data[3],
                ord=exon_data[1],
            )
            self.session.add(exon)
        self.session.commit()

        cf = configparser.ConfigParser()
        cf.add_section("uta")
        cf.set("uta", "admin_role", "uta_admin")

        # load data from test exonsets file.
        with patch(
            "uta.loading._get_seqfetcher",
            return_value=Mock(fetch=Mock(return_value="FAKESEQUENCE")),
        ), patch("uta.loading.logger") as mock_logger:
            ul.load_exonset(self.session, {"FILE": "tests/data/exonsets.mm-exons.gz"}, cf)

            assert mock_logger.warning.called_with(
                "Exon structure mismatch: 4 exons in transcript NM_001005484.2; 3 in alignment NC_000001.11"
            )
            assert mock_logger.warning.called_with(
                "Exon structure mismatch: 1 exons in transcript NM_000864.5; 2 in alignment NC_000001.11"
            )

        # check that the exons for NM_000864.5 and NM_001005484.2 were not loaded,
        # and NM_000911.4 and NM_001005277.1 were loaded
        for tx_ac, expected_exon_count in [("NM_000911.4", 3), ("NM_001005277.1", 1)]:
            exon_set = (
                self.session.query(usam.ExonSet)
                .filter(
                    usam.ExonSet.tx_ac == tx_ac,
                    usam.ExonSet.alt_ac == "NC_000001.11",
                    usam.ExonSet.alt_aln_method == "splign",
                )
                .one()
            )
            exons = (
                self.session.query(usam.Exon)
                .filter(usam.Exon.exon_set_id == exon_set.exon_set_id)
                .all()
            )
            self.assertEqual(len(exons), expected_exon_count)

        for tx_ac in ["NM_000864.5", "NM_001005484.2"]:
            with self.assertRaises(sa.orm.exc.NoResultFound):
                self.session.query(usam.ExonSet).filter(
                    usam.ExonSet.tx_ac == tx_ac,
                    usam.ExonSet.alt_ac == "NC_000001.11",
                    usam.ExonSet.alt_aln_method == "splign",
                ).one()


class TestUtaLoadingFunctions(unittest.TestCase):
    def test__create_translation_exceptions(self):
        transl_except_list = ['(pos:333..335,aa:Sec)', '(pos:1017,aa:TERM)']
        translation_exceptions = ul._create_translation_exceptions(transcript='dummy_tx', transl_except_list=transl_except_list)
        self.assertEqual(translation_exceptions, [
            {
                'tx_ac': 'dummy_tx',
                'start_position': 332,
                'end_position': 335,
                'amino_acid': 'Sec',
            },
            {
                'tx_ac': 'dummy_tx',
                'start_position': 1016,
                'end_position': 1017,
                'amino_acid': 'TERM',
            },
        ])
