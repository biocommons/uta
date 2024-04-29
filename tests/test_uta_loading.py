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
        self.db = testing.postgresql.Postgresql()
        self.session = uta.connect(self.db.url())
        schema = usam.schema_name
        self.session.execute(sa.text(f'drop schema if exists {schema} cascade'))
        self.session.execute(sa.text(f'create schema {schema}'))
        self.session.execute(sa.text('create role uta_admin'))
        self.session.execute(sa.text(f'grant all privileges on schema {schema} to uta_admin'))
        self.session.commit()

        # create all uta tables
        usam.Base.metadata.create_all(self.session.bind.engine)
        self.session.execute(sa.text(f'grant all privileges on all tables in schema {schema} to uta_admin'))
        self.session.execute(sa.text(f'grant all privileges on all sequences in schema {schema} to uta_admin'))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.db.stop(_signal=signal.SIGKILL)
        self.db.cleanup()

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
        self.session.add(g1)

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
                'codon_table': 1,
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
