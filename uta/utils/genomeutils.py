chr_size = {
    'chr1':                   249250621,    'chr2':                   243199373,
    'chr3':                   198022430,    'chr4':                   191154276,
    'chr5':                   180915260,    'chr6':                   171115067,
    'chr7':                   159138663,    'chr8':                   146364022,
    'chr9':                   141213431,    'chr10':                  135534747,
    'chr11':                  135006516,    'chr12':                  133851895,
    'chr13':                  115169878,    'chr14':                  107349540,
    'chr15':                  102531392,    'chr16':                   90354753,
    'chr17':                   81195210,    'chr18':                   78077248,
    'chr20':                   63025520,    'chr19':                   59128983,
    'chr22':                   51304566,    'chr21':                   48129895,
    'chrX':                   155270560,    'chrY':                    59373566,
    'chrM':                       16571,

    'chr11_gl000202_random':      40103,    'chr17_ctg5_hap1':          1680828,
    'chr17_gl000203_random':      37498,    'chr17_gl000204_random':      81310,
    'chr17_gl000205_random':     174588,    'chr17_gl000206_random':      41001,
    'chr18_gl000207_random':       4262,    'chr19_gl000208_random':      92689,
    'chr19_gl000209_random':     159169,    'chr1_gl000191_random':      106433,
    'chr1_gl000192_random':      547496,    'chr21_gl000210_random':      27682,
    'chr4_ctg9_hap1':            590426,    'chr4_gl000193_random':      189789,
    'chr4_gl000194_random':      191469,    'chr6_apd_hap1':            4622290,
    'chr6_cox_hap2':            4795371,    'chr6_dbb_hap3':            4610396,
    'chr6_mann_hap4':           4683263,    'chr6_mcf_hap5':            4833398,
    'chr6_qbl_hap6':            4611984,    'chr6_ssto_hap7':           4928567,
    'chr7_gl000195_random':      182896,    'chr8_gl000196_random':       38914,
    'chr8_gl000197_random':       37175,    'chr9_gl000198_random':       90085,
    'chr9_gl000199_random':      169874,    'chr9_gl000200_random':      187035,
    'chr9_gl000201_random':       36148,    'chrUn_gl000211':            166566,
    'chrUn_gl000212':            186858,    'chrUn_gl000213':            164239,
    'chrUn_gl000214':            137718,    'chrUn_gl000215':            172545,
    'chrUn_gl000216':            172294,    'chrUn_gl000217':            172149,
    'chrUn_gl000218':            161147,    'chrUn_gl000219':            179198,
    'chrUn_gl000220':            161802,    'chrUn_gl000221':            155397,
    'chrUn_gl000222':            186861,    'chrUn_gl000223':            180455,
    'chrUn_gl000224':            179693,    'chrUn_gl000225':            211173,
    'chrUn_gl000226':             15008,    'chrUn_gl000227':            128374,
    'chrUn_gl000228':            129120,    'chrUn_gl000229':             19913,
    'chrUn_gl000230':             43691,    'chrUn_gl000231':             27386,
    'chrUn_gl000232':             40652,    'chrUn_gl000233':             45941,
    'chrUn_gl000234':             40531,    'chrUn_gl000235':             34474,
    'chrUn_gl000236':             41934,    'chrUn_gl000237':             45867,
    'chrUn_gl000238':             39939,    'chrUn_gl000239':             33824,
    'chrUn_gl000240':             41933,    'chrUn_gl000241':             42152,
    'chrUn_gl000242':             43523,    'chrUn_gl000243':             43341,
    'chrUn_gl000244':             39929,    'chrUn_gl000245':             36651,
    'chrUn_gl000246':             38154,    'chrUn_gl000247':             36422,
    'chrUn_gl000248':             39786,    'chrUn_gl000249':             38502,
    }

NC_to_chr = {
    'NC_000001.10':  '1', 'NC_000002.11':  '2', 'NC_000003.11': '3',
    'NC_000004.11':  '4', 'NC_000005.9' :  '5', 'NC_000006.11': '6',
    'NC_000007.13':  '7', 'NC_000008.10':  '8', 'NC_000009.11': '9',
    'NC_000010.10': '10', 'NC_000011.9' : '11', 'NC_000012.11': '12',
    'NC_000013.10': '13', 'NC_000014.8' : '14', 'NC_000015.9' : '15',
    'NC_000016.9' : '16', 'NC_000017.10': '17', 'NC_000018.9' : '18',
    'NC_000019.9' : '19', 'NC_000020.10': '20', 'NC_000021.8' : '21',
    'NC_000022.10': '22', 'NC_000023.10':  'X', 'NC_000024.9' : 'Y',
    }


# also map unversioned accessions
# NC_to_chr.update([ (k.partition('.')[0],v) for k,v in NC_to_chr.iteritems() ])
chr_to_NC = dict([ (v,k) for k,v in NC_to_chr.iteritems() ])

def prepend_chr(chr):
    """prefix chr with 'chr' if not present"""
    return chr if chr[0:3] == 'chr' else 'chr'+chr

def strip_chr(chr):
    """remove 'chr' prefix if it exists"""
    return chr[3:] if chr[0:3] == 'chr' else chr        

# def bracket_region(left,left_margin=0,right=left,right_margin=left_margin):
#     """expand region [left,right) by left_margin (or left_margin and
#     right_margin); returns <left,right>; see clamp_region to 
#     truncate to valid chromosomal region"""
#     right = right or left
#     right_margin = right_margin or left_margin
#     return left-left_margin, right+right_margin
# 
# def clamp_region(chr,left,right):
#     """truncate region to valid chromosomal coordinates"""
#     return max(left,0), min(right,chr_size[prepend_chr(chr)])


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
