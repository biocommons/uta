import Bio.Seq

def chr22XY(c):
    """force to name in chr1..chr22, chrX, chrY, chrM"""
    if c[0:3] == 'chr':
        c = c[3:]
    if c == '23': c = 'X'
    if c == '24': c = 'Y'
    return 'chr'+c

def reverse_complement(seq):
    """return reverse complement of DNA seq
    >>>reverse_complement('AATGGC')
    'GCCATT'
    """
    return Bio.Seq.Seq(seq).reverse_complement().tostring()

def prepend_chr(chr):
    """prefix chr with 'chr' if not present
    >>> prepend_chr('22')
    'chr22'
    >>> prepend_chr('chr22')
    'chr22'
    """
    return chr if chr[0:3] == 'chr' else 'chr'+chr

def strip_chr(chr):
    """remove 'chr' prefix if it exists
    >>> strip_chr('22')
    '22'
    >>> strip_chr('chr22')
    '22'
    """
    return chr[3:] if chr[0:3] == 'chr' else chr        


def url_for_slice(c,s,e):
    url_fmt = (
        'http://www.ncbi.nlm.nih.gov/projects/sviewer/?id={nc}'
        '&noslider=1&tracks=[key:sequence_track,name:Sequence,'
        'display_name:Sequence,category:Sequence,annots:Sequence'
        ',ShowLabel:false][key:gene_model_track,name:Genes---Unnamed'
        ',display_name:Genes,category:Genes,annots:Unnamed,Options'
        ':MergeAll,SNPs:false,CDSProductFeats:false,'
        'ShowLabelsForAllFeatures:false,HighlightMode:2][key:'
        'alignment_track,name:Alignments---NG%20Alignments,'
        'display_name:NG%20Alignments,category:Alignments,'
        'annots:NG%20Alignments,Layout:Adaptive1000,StatDisplay'
        ':-1,LinkMatePairAligns:true,Color:true,AlignedSeqFeats'
        ':false,Label:true][key:alignment_track,name:Alignments'
        '---Refseq%20Alignments,display_name:Refseq%20Alignments'
        ',category:Alignments,annots:Refseq%20Alignments,Layout'
        ':Adaptive1000,StatDisplay:-1,LinkMatePairAligns:true'
        ',Color:true,AlignedSeqFeats:false,Label:true]&mk=&color'
        '=0&label=0&decor=0&spacing=0&v={start}:{end}&c='
        '33cccc&gflip=false&select='
        'gi|224589812-0390e571-039b5700-0103-dee8c202-ffea8d58'
        )
    nc = chr_to_NC[strip_chr(c)]
    url = url_fmt.format(nc=nc,  start=str(s), end=str(e))
    return url


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
