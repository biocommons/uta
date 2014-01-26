import ConfigParser
import os
import unittest

import sqlalchemy as sa
import sqlalchemy.schema as sas
import sqlalchemy.orm as sao
import sqlalchemy.ext.declarative as saed

import uta.db.sa_models as usam

data_dir = os.path.realpath(os.path.realpath( os.path.join(__file__,'../data')))
cp = ConfigParser.SafeConfigParser()
cp.readfp( open( os.path.join(data_dir,'test.conf') ) )


class Test_uta_sa_models(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print( "testing against " + cp.get('uta','db_url') )
        engine = sa.create_engine(cp.get('uta','db_url'))
        engine.execute('DROP SCHEMA IF EXISTS ' + usam.schema_name + ' CASCADE')
        engine.execute(sas.CreateSchema(usam.schema_name))

        Session = sao.sessionmaker(bind = engine)
        self.session = Session()

        usam.Base.metadata.create_all(engine) 
        self.session.commit()

        o = usam.Origin(
            name = 'Testing (originally NCBI, via Eutils)',
            url = 'http://bogus.com/',
            url_ac_fmt = 'http://bogus.com/{ac}',
            )
        self.session.add(o)

        # Test data are from:
        # http://www.ncbi.nlm.nih.gov/nuccore/NM_033304.2

        g = usam.Gene(
            hgnc = 'ADRA1A',
            maploc = '8p21.2',
            strand = -1,
            descr   = 'adrenoceptor alpha 1A',
            summary = '''Alpha-1-adrenergic receptors (alpha-1-ARs) are
            members of the G protein-coupled receptor superfamily. They
            activate mitogenic responses and regulate growth and proliferation
            of many cells. There are 3 alpha-1-AR subtypes: alpha-1A, -1B and
            -1D, all of which signal through the Gq/11 family of G-proteins
            and different subtypes show different patterns of activation. This
            gene encodes alpha-1A-adrenergic receptor. Alternative splicing of
            this gene generates four transcript variants, which encode four
            different isoforms with distinct C-termini but having similar
            ligand binding properties. [provided by RefSeq, Jul 2008]'''.replace('\n',' ')
            )
        self.session.add(g)

        chr8_n = usam.DNASeq(
            seq = None,
            )
        self.session.add(chr8_n)

        dsoa_n = usam.DNASeqOriginAlias(
            dnaseq_id = chr8_n,
            origin = o,
            alias = 'NC_000008.10',
            )

        transcripts = {
            'NM_000680.2': {
                'seq': 'gaattccgaatcatgtgcagaatgctgaatcttcccccagccaggacgaataagacagcgcggaaaagcagattctcgtaattctggaattgcatgttgcaaggagtctcctggatcttcgcacccagcttcgggtagggagggagtccgggtcccgggctaggccagcccggcaggtggagagggtccccggcagccccgcgcgcccctggccatgtctttaatgccctgccccttcatgtggccttctgagggttcccagggctggccagggttgtttcccacccgcgcgcgcgctctcacccccagccaaacccacctggcagggctccctccagccgagaccttttgattcccggctcccgcgctcccgcctccgcgccagcccgggaggtggccctggacagccggacctcgcccggccccggctgggaccatggtgtttctctcgggaaatgcttccgacagctccaactgcacccaaccgccggcaccggtgaacatttccaaggccattctgctcggggtgatcttggggggcctcattcttttcggggtgctgggtaacatcctagtgatcctctccgtagcctgtcaccgacacctgcactcagtcacgcactactacatcgtcaacctggcggtggccgacctcctgctcacctccacggtgctgcccttctccgccatcttcgaggtcctaggctactgggccttcggcagggtcttctgcaacatctgggcggcagtggatgtgctgtgctgcaccgcgtccatcatgggcctctgcatcatctccatcgaccgctacatcggcgtgagctacccgctgcgctacccaaccatcgtcacccagaggaggggtctcatggctctgctctgcgtctgggcactctccctggtcatatccattggacccctgttcggctggaggcagccggcccccgaggacgagaccatctgccagatcaacgaggagccgggctacgtgctcttctcagcgctgggctccttctacctgcctctggccatcatcctggtcatgtactgccgcgtctacgtggtggccaagagggagagccggggcctcaagtctggcctcaagaccgacaagtcggactcggagcaagtgacgctccgcatccatcggaaaaacgccccggcaggaggcagcgggatggccagcgccaagaccaagacgcacttctcagtgaggctcctcaagttctcccgggagaagaaagcggccaaaacgctgggcatcgtggtcggctgcttcgtcctctgctggctgccttttttcttagtcatgcccattgggtctttcttccctgatttcaagccctctgaaacagtttttaaaatagtattttggctcggatatctaaacagctgcatcaaccccatcatatacccatgctccagccaagagttcaaaaaggcctttcagaatgtcttgagaatccagtgtctctgcagaaagcagtcttccaaacatgccctgggctacaccctgcacccgcccagccaggccgtggaagggcaacacaaggacatggtgcgcatccccgtgggatcaagagagaccttctacaggatctccaagacggatggcgtttgtgaatggaaatttttctcttccatgccccgtggatctgccaggattacagtgtccaaagaccaatcctcctgtaccacagcccgggtgagaagtaaaagctttttgcaggtctgctgctgtgtagggccctcaacccccagccttgacaagaaccatcaagttccaaccattaaggtccacaccatctccctcagtgagaacggggaggaagtctaggacaggaaagatgcagaggaaaggggaataatcttaggtacccaccccacttccttctcggaaggccagctcttcttggaggacaagacaggaccaatcaaagaggggacctgctgggaatggggtgggtggtagacccaactcatcaggcagcgggtagggcacagggaagagggagggtgtctcacaaccaaccagttcagaatgatacggaacagcatttccctgcagctaatgctttcttggtcactctgtgcccacttcaacgaaaaccaccatgggaaacagaatttcatgcacaatccaaaagactataaatataggattatgatttcatcatgaatattttgagcacacactctaagtttggagctatttcttgatggaagtgaggggattttattttcaggctcaacctactgacagccacatttgacatttatg',
                't_starts_i': [0,1319], 			't_ends_i': [1319,2281],			'names': ['1','2b'],
                't_cds_start_i': 436, 				't_cds_end_i': 1837,
                'g_strand': -1,
                'g_starts_i': [26721603,26627221], 		'g_ends_i': [26722922,26628183],
                'g_cds_start_i': 26627665, 			'g_cds_end_i': 26722486,
                },
            'NM_033302.2': {
                'seq': 'gaattccgaatcatgtgcagaatgctgaatcttcccccagccaggacgaataagacagcgcggaaaagcagattctcgtaattctggaattgcatgttgcaaggagtctcctggatcttcgcacccagcttcgggtagggagggagtccgggtcccgggctaggccagcccggcaggtggagagggtccccggcagccccgcgcgcccctggccatgtctttaatgccctgccccttcatgtggccttctgagggttcccagggctggccagggttgtttcccacccgcgcgcgcgctctcacccccagccaaacccacctggcagggctccctccagccgagaccttttgattcccggctcccgcgctcccgcctccgcgccagcccgggaggtggccctggacagccggacctcgcccggccccggctgggaccatggtgtttctctcgggaaatgcttccgacagctccaactgcacccaaccgccggcaccggtgaacatttccaaggccattctgctcggggtgatcttggggggcctcattcttttcggggtgctgggtaacatcctagtgatcctctccgtagcctgtcaccgacacctgcactcagtcacgcactactacatcgtcaacctggcggtggccgacctcctgctcacctccacggtgctgcccttctccgccatcttcgaggtcctaggctactgggccttcggcagggtcttctgcaacatctgggcggcagtggatgtgctgtgctgcaccgcgtccatcatgggcctctgcatcatctccatcgaccgctacatcggcgtgagctacccgctgcgctacccaaccatcgtcacccagaggaggggtctcatggctctgctctgcgtctgggcactctccctggtcatatccattggacccctgttcggctggaggcagccggcccccgaggacgagaccatctgccagatcaacgaggagccgggctacgtgctcttctcagcgctgggctccttctacctgcctctggccatcatcctggtcatgtactgccgcgtctacgtggtggccaagagggagagccggggcctcaagtctggcctcaagaccgacaagtcggactcggagcaagtgacgctccgcatccatcggaaaaacgccccggcaggaggcagcgggatggccagcgccaagaccaagacgcacttctcagtgaggctcctcaagttctcccgggagaagaaagcggccaaaacgctgggcatcgtggtcggctgcttcgtcctctgctggctgccttttttcttagtcatgcccattgggtctttcttccctgatttcaagccctctgaaacagtttttaaaatagtattttggctcggatatctaaacagctgcatcaaccccatcatatacccatgctccagccaagagttcaaaaaggcctttcagaatgtcttgagaatccagtgtctctgcagaaagcagtcttccaaacatgccctgggctacaccctgcacccgcccagccaggccgtggaagggcaacacaaggacatggtgcgcatccccgtgggatcaagagagaccttctacaggatctccaagacggatggcgtttgtgaatggaaatttttctcttccatgccccgtggatctgccaggattacagtgtccaaagaccaatcctcctgtaccacagcccggggacacacacccatgacatgaagccagcttcccgtccacgactgttgtccttactgcccaaggaaggggagcatgaaacccaccactggtcctgcgacccactgtctttggaatccaccccaggagcccaggagccttgcctgacacttggatttacttctttatcaagcatccatctgactaaggcacaaatccaacatgttactgttactgatacaggaaaaacagtaacttaaggaatgatcatgaatgcaaagggaaagaggaaaagagccttcagggacaaatagctcgattttttgtaaatcagtttcatacaacctccctcccccatttcattcttaaaagttaattgagaatcatcagccacgtgtagggtgtgag',
                't_starts_i': [0,1319,1705], 			't_ends_i': [1319,1705,2089], 			'names': ['1','2a','4'],
                't_cds_start_i': 436, 				't_cds_end_i': 1726,
                'g_strand': -1,
                'g_starts_i': [26721603,26627797,26613912], 	'g_ends_i': [26722922,26628183,26614296],
                'g_cds_start_i': 26614275, 			'g_cds_end_i': 26722486,
                },
            'NM_033303.3': {
                'seq': 'gaattccgaatcatgtgcagaatgctgaatcttcccccagccaggacgaataagacagcgcggaaaagcagattctcgtaattctggaattgcatgttgcaaggagtctcctggatcttcgcacccagcttcgggtagggagggagtccgggtcccgggctaggccagcccggcaggtggagagggtccccggcagccccgcgcgcccctggccatgtctttaatgccctgccccttcatgtggccttctgagggttcccagggctggccagggttgtttcccacccgcgcgcgcgctctcacccccagccaaacccacctggcagggctccctccagccgagaccttttgattcccggctcccgcgctcccgcctccgcgccagcccgggaggtggccctggacagccggacctcgcccggccccggctgggaccatggtgtttctctcgggaaatgcttccgacagctccaactgcacccaaccgccggcaccggtgaacatttccaaggccattctgctcggggtgatcttggggggcctcattcttttcggggtgctgggtaacatcctagtgatcctctccgtagcctgtcaccgacacctgcactcagtcacgcactactacatcgtcaacctggcggtggccgacctcctgctcacctccacggtgctgcccttctccgccatcttcgaggtcctaggctactgggccttcggcagggtcttctgcaacatctgggcggcagtggatgtgctgtgctgcaccgcgtccatcatgggcctctgcatcatctccatcgaccgctacatcggcgtgagctacccgctgcgctacccaaccatcgtcacccagaggaggggtctcatggctctgctctgcgtctgggcactctccctggtcatatccattggacccctgttcggctggaggcagccggcccccgaggacgagaccatctgccagatcaacgaggagccgggctacgtgctcttctcagcgctgggctccttctacctgcctctggccatcatcctggtcatgtactgccgcgtctacgtggtggccaagagggagagccggggcctcaagtctggcctcaagaccgacaagtcggactcggagcaagtgacgctccgcatccatcggaaaaacgccccggcaggaggcagcgggatggccagcgccaagaccaagacgcacttctcagtgaggctcctcaagttctcccgggagaagaaagcggccaaaacgctgggcatcgtggtcggctgcttcgtcctctgctggctgccttttttcttagtcatgcccattgggtctttcttccctgatttcaagccctctgaaacagtttttaaaatagtattttggctcggatatctaaacagctgcatcaaccccatcatatacccatgctccagccaagagttcaaaaaggcctttcagaatgtcttgagaatccagtgtctctgcagaaagcagtcttccaaacatgccctgggctacaccctgcacccgcccagccaggccgtggaagggcaacacaaggacatggtgcgcatccccgtgggatcaagagagaccttctacaggatctccaagacggatggcgtttgtgaatggaaatttttctcttccatgccccgtggatctgccaggattacagtgtccaaagaccaatcctcctgtaccacagcccggacgaagtctcgctctgtcaccaggctggagtgcagtggcatgatcttggctcactgcaacctccgcctcccgggttcaagagattctcctgcctcagcctcccaagcagctgggactacagggatgtgccaccaggccgacgccaccaggcccagctaatttttgtatttttagtagagacggggtttcaccatgttggccaggatgatctcgatctcttgacctcatgatctgcctgcctcagcctcccaaagtgctgggattacaggcgtgagccaccgtgcccggcccaactattttttttttttatcttttttaacagtgcaatcctttctgtggatgaaatcttgctcagaagctcaatatgcaaaagaaagaaaaacagcagggctggacggatgttgggagtggggtaagaccccaaccactcagaaccacccccccaacacacacacacattctctccatggtgactggtgaggggcctctagagggtacatagtacaccatggagcacggtttaagcaccactggactacacattcttctgtggcagttatcttaccttcccatagacacccagcccatagccattggtt',
                't_starts_i': [0,1319,1705], 			't_ends_i': [1319,1705,2304], 			'names': ['1','2a','5'],
                't_cds_start_i': 436, 				't_cds_end_i': 1864,
                'g_strand': -1,
                'g_starts_i': [26721603,26627797,26605666], 	'g_ends_i': [26722922,26628183,26606265],
                'g_cds_start_i': 26606106, 			'g_cds_end_i': 26722486,
                },
            'NM_033304.2': {
                'seq': 'gaattccgaatcatgtgcagaatgctgaatcttcccccagccaggacgaataagacagcgcggaaaagcagattctcgtaattctggaattgcatgttgcaaggagtctcctggatcttcgcacccagcttcgggtagggagggagtccgggtcccgggctaggccagcccggcaggtggagagggtccccggcagccccgcgcgcccctggccatgtctttaatgccctgccccttcatgtggccttctgagggttcccagggctggccagggttgtttcccacccgcgcgcgcgctctcacccccagccaaacccacctggcagggctccctccagccgagaccttttgattcccggctcccgcgctcccgcctccgcgccagcccgggaggtggccctggacagccggacctcgcccggccccggctgggaccatggtgtttctctcgggaaatgcttccgacagctccaactgcacccaaccgccggcaccggtgaacatttccaaggccattctgctcggggtgatcttggggggcctcattcttttcggggtgctgggtaacatcctagtgatcctctccgtagcctgtcaccgacacctgcactcagtcacgcactactacatcgtcaacctggcggtggccgacctcctgctcacctccacggtgctgcccttctccgccatcttcgaggtcctaggctactgggccttcggcagggtcttctgcaacatctgggcggcagtggatgtgctgtgctgcaccgcgtccatcatgggcctctgcatcatctccatcgaccgctacatcggcgtgagctacccgctgcgctacccaaccatcgtcacccagaggaggggtctcatggctctgctctgcgtctgggcactctccctggtcatatccattggacccctgttcggctggaggcagccggcccccgaggacgagaccatctgccagatcaacgaggagccgggctacgtgctcttctcagcgctgggctccttctacctgcctctggccatcatcctggtcatgtactgccgcgtctacgtggtggccaagagggagagccggggcctcaagtctggcctcaagaccgacaagtcggactcggagcaagtgacgctccgcatccatcggaaaaacgccccggcaggaggcagcgggatggccagcgccaagaccaagacgcacttctcagtgaggctcctcaagttctcccgggagaagaaagcggccaaaacgctgggcatcgtggtcggctgcttcgtcctctgctggctgccttttttcttagtcatgcccattgggtctttcttccctgatttcaagccctctgaaacagtttttaaaatagtattttggctcggatatctaaacagctgcatcaaccccatcatatacccatgctccagccaagagttcaaaaaggcctttcagaatgtcttgagaatccagtgtctctgcagaaagcagtcttccaaacatgccctgggctacaccctgcacccgcccagccaggccgtggaagggcaacacaaggacatggtgcgcatccccgtgggatcaagagagaccttctacaggatctccaagacggatggcgtttgtgaatggaaatttttctcttccatgccccgtggatctgccaggattacagtgtccaaagaccaatcctcctgtaccacagcccggaggggaatggattgtagatatttcaccaagaattgcagagagcatatcaagcatgtgaattttatgatgccaccgtggagaaagggttcagaatgctgatctccaggtagctggagacctaggcagtctgcaaatgaggagtcagctggaagctatggctatgtattatgtgacatcgcttgttcctaagtgaaaactggatatcccaaccttctggcccagtaggtttcatggttaagacctggtagtgagaacattttaggaactatttgcttgggcaggcaatttttcactct',
                't_starts_i': [0,1319,1705], 			't_ends_i': [1319,1705,2001], 			'names': ['1','2a','3'],
                't_cds_start_i': 436, 				't_cds_end_i': 1804,
                'g_strand': -1,
                'g_starts_i': [26721603,26627797,26623370], 	'g_ends_i': [26722922,26628183,26623666],
                'g_cds_start_i': 26623567, 			'g_cds_end_i': 26722486,
                },
            }

        for ac,tx_info in transcripts.iteritems():
            n = usam.DNASeq(
                seq = tx_info['seq']
                )
            n.origin = o
            self.session.add(n)

            t = usam.Transcript(
                ac = ac,
                gene_id = g.gene_id,
                strand = 1,
                cds_start_i = tx_info['t_cds_start_i'],
                cds_end_i = tx_info['t_cds_end_i'],
                )
            t.origin = o
            t.dnaseq = n
            t.gene = g
            self.session.add(t)

            # ExonSet and Exons on Transcript seq
            t_es = usam.ExonSet(
                origin = o,
                transcript = t,
                strand = 1,
                method = 'test',
                )
            t_es.ref_dnaseq = n
            self.session.add(t_es)

            for se in zip(tx_info['t_starts_i'],tx_info['t_ends_i'],tx_info['names']):
                e = usam.Exon(
                    start_i = se[0],
                    end_i = se[1],
                    name = se[2],
                    )
                e.exon_set = t_es
                self.session.add(e)

            # ExonSet and Exons on chromosome seq
            g_es = usam.ExonSet(
                strand = tx_info['g_strand'],
                cds_start_i = tx_info['g_cds_start_i'],
                cds_end_i = tx_info['g_cds_end_i'],
                origin = o,
                transcript = t,
                ref_dnaseq = chr8_n,
                )
            self.session.add(g_es)

            for se in zip(tx_info['g_starts_i'],tx_info['g_ends_i']):
                e = usam.Exon(
                    start_i = se[0],
                    end_i = se[1],
                    )
                e.exon_set = g_es
                self.session.add(e)

        self.session.commit()


    def test_origin(self):
        all_origins = self.session.query(usam.Origin).all()
        self.assertEqual( len(all_origins), 1 )

        o = all_origins[0]
        self.assertRegexpMatches(o.name, 'Testing')
        self.assertEquals(o.url, 'http://bogus.com/')
        self.assertEquals(o.url_ac_fmt, 'http://bogus.com/{ac}')

        self.assertEqual( len(o.transcripts), 4 ) ## NM_000680.2, NM_033302.2, NM_033303.3, NM_033304.2
        self.assertEqual( len(o.dnaseqs)      , 5 ) ## NC_000008.10, + transcripts
        self.assertEqual( len(o.exon_sets)  , 8 ) ## 4 transcripts * {genomic,transcript}

    def test_gene(self):
        all_genes = self.session.query(usam.Gene).all()
        self.assertEqual( len(all_genes), 1 )

        g = all_genes[0]
        self.assertEqual( g.descr, u'adrenoceptor alpha 1A' )
        self.assertEqual( g.maploc, u'8p21.2' )
        self.assertEqual( g.strand, -1 )
        self.assertEqual( g.strand_pm, u'-' )
        self.assertEqual( len(g.transcripts), 4 )
        self.assertTrue( g.summary.startswith('Alpha-1-adrenergic receptors (alpha-1-ARs) are') )

    def test_dnaseq(self):
        all_dnaseqs = self.session.query(usam.DNASeq).all()
        self.assertEqual( len(all_dnaseqs), 5 )
        
        n = self.session.query(usam.DNASeq).filter(usam.DNASeq.ac == 'NC_000008.10').one()
        self.assertEquals(n.ac, u'NC_000008.10')
        self.assertTrue(len(n.exon_sets),2)
        self.assertRegexpMatches(n.origin.name, '^Testing')
        #self.assertEquals(len(n.transcripts), 0)

        n = self.session.query(usam.DNASeq).filter(usam.DNASeq.ac == 'NM_000680.2').one()
        self.assertEquals(n.ac, u'NM_000680.2')
        self.assertTrue(len(n.exon_sets),1)
        self.assertEquals(n.md5, u'829f098bb244c1370befd6d448b6c9ad')
        self.assertRegexpMatches(n.origin.name, '^Testing')
        self.assertEquals(len(n.seq), 2281)
        self.assertTrue(n.seq.startswith('gaattccgaa'))
        self.assertTrue(n.seq.endswith('gacatttatg'))
        #self.assertEquals(len(n.transcripts), 1)
        
    def test_exon_set(self):
        all_exon_sets = self.session.query(usam.DNASeq).all()
        self.assertTrue(len(all_exon_sets),8)
        
        exon_sets = self.session.query(usam.Transcript).filter(usam.Transcript.ac=='NM_000680.2').one().exon_sets

        # http://www.ncbi.nlm.nih.gov/nuccore/NM_000680.2
        es = [ es for es in exon_sets if es.is_primary ][0]
        self.assertEquals( (es.cds_start_i,es.cds_end_i), (436, 1837) )
        self.assertEquals( len(es.exons), 2 )
        self.assertEquals( es.is_primary, True )
        self.assertEquals( es.ref_dnaseq.ac, 'NM_000680.2' )
        self.assertEquals( es.strand, 1 )
        self.assertEquals( es.transcript.ac, 'NM_000680.2' )

        # seq_gene.md.gz:
        # 9606	8	26627222	26627665	-	NT_167187.1	14485368	14485811	-	NM_000680.2	GeneID:148	UTR	GRCh37.p10-Primary Assembly	NM_000680.2	-
        # 9606	8	26627666	26628183	-	NT_167187.1	14485812	14486329	-	NP_000671.2	GeneID:148	CDS	GRCh37.p10-Primary Assembly	NM_000680.2	-
        # 9606	8	26721604	26722486	-	NT_167187.1	14579750	14580632	-	NP_000671.2	GeneID:148	CDS	GRCh37.p10-Primary Assembly	NM_000680.2	-
        # 9606	8	26722487	26722922	-	NT_167187.1	14580633	14581068	-	NM_000680.2	GeneID:148	UTR	GRCh37.p10-Primary Assembly	NM_000680.2	-
        es = [ es for es in exon_sets if not es.is_primary ][0]
        self.assertEquals( (es.cds_start_i,es.cds_end_i), (26627665, 26722486) )
        self.assertEquals( len(es.exons), 2 )
        self.assertEquals( es.is_primary, False )
        self.assertEquals( es.ref_dnaseq.ac, 'NC_000008.10' )
        self.assertEquals( es.strand, -1 )
        self.assertEquals( es.transcript.ac, 'NM_000680.2' )

    def test_exon(self):
        t = self.session.query(usam.Transcript).filter(usam.Transcript.ac=='NM_000680.2').one()
        es = [ es for es in t.exon_sets if es.is_primary ][0]
        self.assertEqual( (es.exons[0].start_i,es.exons[0].end_i) , (0,1319) )
        self.assertEqual( (es.exons[1].start_i,es.exons[1].end_i) , (1319,2281) )


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
