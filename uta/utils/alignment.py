import itertools

import Bio.AlignIO
import Bio.Emboss.Applications as bea
import cStringIO


## I haven't figured out a nice way to test align2() conditionally based
## on whether needle is available. Since the code exists mostly for
## historical comparison, it's now commented out.

def align2(seqa,seqb,gapopen=10,gapextend=0.5):
    """Globally align two sequences.
    This function currently uses EMBOSS' needle command, which ideally
    would be replaced by a forkless version in Python.

    >>> seq1 = 'acacagccattaatcttgtagcttcatattaactggtttgctttcatgacgctgctgaggaat'
    >>> seq2 = 'acagacccattaatcttgtagcttcatcaacattaactggtttgctttcatgacaggaat'

    # TODO: Work out conditional test based on whether emboss is available
    # >>> a1,a2 = align2(seq1,seq2)
    # >>> a1
    # 'acacagccattaatcttgtagcttcat----attaactggtttgctttcatgacgctgctgaggaat'
    # >>> a2
    # 'acagacccattaatcttgtagcttcatcaacattaactggtttgctttcatgac-------aggaat'

    """
    if seqa == seqb:
        return seqa, seqb
    cline = bea.NeedleCommandline(asequence='asis:'+seqa, bsequence='asis:'+seqb,
                                  gapopen=gapopen,gapextend=gapextend,
                                  auto=True,filter=True,stdout=True)
    o, e = cline()
    aln = Bio.AlignIO.read(cStringIO.StringIO(o), 'emboss')
    return aln[0].seq.tostring(), aln[1].seq.tostring()


def alignment_match_string(aseq1,aseq2):
    """for aligned sequences aseq1 and aseq2, both of length n, return an
    exploded CIGAR string of length n with characters denoting M)atch,
    I)nsertion, D)eletion, X)mismatch of aseq2 relative to aseq1.  In our
    case, M always means identity match; in general, M may mean
    match/mismatch under some substitution matrix.  See
    http://goo.gl/fek4t for a short summary.

    >>> aseq1 = 'acacagccattaatcttgtagcttcat----attaactggtttgctttcatgacgctgctgaggaat'
    >>> aseq2 = 'acagacccattaatcttgtagcttcatcaacattaactggtttgctttcatgac-------aggaat'
    >>> alignment_match_string( aseq1,aseq2 )
    'MMMXMXMMMMMMMMMMMMMMMMMMMMMIIIIMMMMMMMMMMMMMMMMMMMMMMMDDDDDDDMMMMMM'

    """
    assert len(aseq1) == len(aseq2)
    def _cigar_char(c1,c2): 
        if c1 == c2:  return 'M'
        if c1 == '-': return 'I' 
        if c2 == '-': return 'D' 
        if c1 != c2:  return 'X'
        raise Exception('In the words of David Byrne, how did I get here?')
    match_string = [ _cigar_char(c1,c2) for c1,c2 in zip(aseq1,aseq2) ]
    return ''.join(match_string)

def alignment_cigar_list(aseq1,aseq2):
    """Return a list of cigar operations for the aligned sequences aseq1
    and aseq2.  Each tuple is (pos, operation, count).
    
    >>> aseq1 = 'acacagccattaatcttgtagcttcat----attaactggtttgctttcatgacgctgctgaggaat'
    >>> aseq2 = 'acagacccattaatcttgtagcttcatcaacattaactggtttgctttcatgac-------aggaat'
    >>> for a in alignment_cigar_list( aseq1,aseq2 ):
    ...   print a
    (0, 'M', 3)
    (3, 'X', 1)
    (4, 'M', 1)
    (5, 'X', 1)
    (6, 'M', 21)
    (27, 'I', 4)
    (31, 'M', 23)
    (54, 'D', 7)
    (61, 'M', 6)

    """
    # compute "cigar vector" (cv), which is really just RLE of edits
    cv = [ (c,len(list(group)))
           for c, group in itertools.groupby(alignment_match_string(aseq1,aseq2)) ]
    # then figure out the start position of each element
    pcv = []
    s = 0
    for e in cv:
        pcv += [ (s,e[0],e[1]) ]
        s += e[1]
    return pcv


def alignment_cigar_string(aseq1, aseq2):
    """return a CIGAR string for aligned sequences aseq1 and aseq2,
    which must be of equal length.

    >>> aseq1 = 'acacagccattaatcttgtagcttcat----attaactggtttgctttcatgacgctgctgaggaat'
    >>> aseq2 = 'acagacccattaatcttgtagcttcatcaacattaactggtttgctttcatgac-------aggaat'
    >>> alignment_cigar_string( aseq1,aseq2 )
    '3M1X1M1X21M4I23M7D6M'

    """
    return ''.join([ str(l)+c 
                     for _,c,l in alignment_cigar_list(aseq1,aseq2) ])

def explode_cigar(cigar):
    """return a vector of column matches for a given cigar string

    >>> explode_cigar('5M2I4X1D')
    'MMMMMIIXXXXD'

    """
    import re
    u = re.compile('(?P<n>\d+)(?P<op>[MXID])')
    return ''.join([ md['op']*int(md['n']) 
                     for md in [m.groupdict() for m in u.finditer(cigar)] ])


if __name__ == "__main__":
    import doctest
    doctest.testmod()


## <LICENSE>
## Copyright 2014 UTA Contributors (https://bitbucket.org/uta/uta)
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
