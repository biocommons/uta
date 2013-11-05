from uta.exceptions import *

def human_to_ci(s,e=None, so=0, eo=0):
    """convert start,end interval in inclusive, discontinuous HGVS coordinates
    (..,-2,-1,1,2,..) to continuous interbase (right-open) coordinates
    (..,-2,-1,0,1,..)"""

    #def _cds_to_ci(c):
    #    assert c != 0, 'received CDS coordinate 0; expected ..,-2,-1,1,1,...'
    #    return c-1 if c>0 else c
    #return _cds_to_ci(s), None if e is None else _cds_to_ci(e)+1

    assert s != 0 and e != 0, 'Received CDS coordinate 0; expected ...,-2,-1,1,1,...'

    # Extra explicit because things get more complicated when dealing with introns
    # so, eo = start offset, end offset
    if so == 0:
        s = s - 1
        so = 0
    elif so > 0:
        s = s
        so = so - 1
    elif so < 0:
        s = s - 1
        so = so
    else:
        raise UTAError('Something went terribly wrong with the start offset coordinate mapping')

    if eo == 0:
        e = e
        eo = 0
    elif eo > 0:
        e = e
        eo = eo
    elif eo < 0:
        assert e is not None, 'Human end coordinate cannot be none'
        e = e - 1
        eo = eo + 1
    else:
        raise UTAError('Something went terribly wrong with the end offset coordinate mapping')

    return s, e, so, eo

def ci_to_human(s,e=None, so=0, eo=0):
    """convert start,end interval in continuous interbase (right-open)
    coordinates (..,-2,-1,0,1,..) to discontinuous HGVS coordinates
    (..,-2,-1,1,2,..)"""

    #def _ci_to_cds(c):
    #    return c+1 if c>=0 else c
    #return _ci_to_cds(s), None if e is None else _ci_to_cds(e)-1, so, eo

    def _ci_to_cds(c):
        return c+1 if c>=0 else c

    # Extra explicit because things get more complicated when dealing with introns
    # so, eo = start offset, end offset
    if so == 0:
        s = s + 1
        so = 0
    elif so > 0:
        s = s
        so = so + 1
    elif so < 0:
        s = s + 1
        so = so
    else:
        raise UTAError('Something went terribly wrong with the start offset coordinate mapping')

    if eo == 0:
        # accounts for negative offsets in introns
        if so >= 0:
            e = e
            eo = 0
        else:
            assert e is not None, 'Human end coordinate cannot be none'
            e = e + 1
            eo = eo - 1
    elif eo > 0:
        e = e
        eo = eo
    elif eo < 0:
        assert e is not None, 'Human end coordinate cannot be none'
        e = e + 1
        eo = eo - 1
    else:
        raise UTAError('Something went terribly wrong with the end offset coordinate mapping')


    return s, e, so, eo


cds_to_ci = human_to_ci
ci_to_cds = ci_to_human
