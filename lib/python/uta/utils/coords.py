def cds_to_ci(s,e=None):
    """convert start,end interval in inclusive, discontinuous HGVS coordinates
    (..,-2,-1,1,2,..) to continuous interbase (right-open) coordinates
    (..,-2,-1,0,1,..)"""
    def _cds_to_ci(c):
        assert c != 0, 'received CDS coordinate 0; expected ..,-2,-1,1,1,...'
        return c-1 if c>0 else c
    return _cds_to_ci(s), None if e is None else _cds_to_ci(e)+1

def ci_to_cds(s,e=None):
    """convert start,end interval in continuous interbase (right-open)
    coordinates (..,-2,-1,0,1,..) to discontinuous HGVS coordinates
    (..,-2,-1,1,2,..)"""
    def _ci_to_cds(c):
        return c+1 if c>=0 else c
    return _ci_to_cds(s), None if e is None else _ci_to_cds(e)-1
