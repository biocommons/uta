import gzip,os,unittest

import uta.parsers.geneinfo

data_dir = os.path.realpath(os.path.realpath( os.path.join(__file__,'../data')))

# gzip -cd misc/data/ftp.ncbi.nih.gov/gene/DATA/gene_info.gz | grep ^9606 | head -101 | gzip -c >tests/data/gene_info_100human.gz

class Test_parsers_geneinfoparser(unittest.TestCase):
    def test1(self):
        fn = os.path.join(data_dir,'gene_info_100human.gz')
        gip = uta.parsers.geneinfo.GeneInfoParser(gzip.open(fn))
        gi = gip.next()
        self.assertEqual(gi, {
                'Full_name_from_nomenclature_authority': 'alpha-1-B glycoprotein',
                'GeneID': '1',
                'LocusTag': '-',
                'Modification_date': '20130609',
                'Nomenclature_status': 'O',
                'Other_designations': 'alpha-1B-glycoprotein',
                'Symbol': 'A1BG',
                'Symbol_from_nomenclature_authority': 'A1BG',
                'Synonyms': 'A1B|ABG|GAB|HYST2477',
                'chromosome': '19',
                'dbXrefs': 'HGNC:5|MIM:138670|Ensembl:ENSG00000121410|HPRD:00726|Vega:OTTHUMG00000183507',
                'description': 'alpha-1-B glycoprotein',
                'map_location': '19q13.4',
                'tax_id': '9606',
                'type_of_gene': 'protein-coding'})


if __name__ == '__main__':
    unittest.main()


