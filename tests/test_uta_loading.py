import configparser
import signal
import unittest

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
