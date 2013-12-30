import gzip,os,unittest

import uta.parsers.seqgene

data_dir = os.path.realpath(os.path.realpath( os.path.join(__file__,'../data')))

# gzip -cd misc/data/ftp.ncbi.nih.gov/gene/DATA/gene_info.gz | grep ^9606 | head -101 | gzip -c >tests/data/gene_info_100human.gz

class Test_parsers_seqgene(unittest.TestCase):
    def test1(self):
        fn = os.path.join(data_dir,'seq_gene_100.md.gz')
        parser = uta.parsers.seqgene.SeqGeneParser(gzip.open(fn))
        rec = parser.next()
        self.assertEqual(rec, {
                'chr_orient': '+',
                'chr_start': '697',
                'chr_stop': '1075',
                'chromosome': '1',
                'contig': 'NW_001838563.2',
                'ctg_orient': '-',
                'ctg_start': '4805',
                'ctg_stop': '5183',
                'evidence_code': '',
                'feature_id': 'GeneID:100887749',
                'feature_name': 'MTND1P23',
                'feature_type': 'GENE',
                'group_label': 'HuRef-Primary Assembly',
                'tax_id': '9606',
                'transcript': '-'})


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
