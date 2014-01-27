def strand_pm(strand):
    if strand is None: return ''
    elif strand == 1: return '+'
    elif strand == -1: return '-'
    else: return '?'

def tx_digest(seq_md5, cds_se_i, exons_se_i):
    def coord_fmt(se):
        return "[{se[0]};{se[1]})".format(se=se)
    tx_info = "{seq_md5};{cds_se_str};[{exon_se_str}]".format(
        seq_md5=seq_md5, cds_se_str=coord_fmt(cds_se_i),
        exon_se_str=";".join([coord_fmt(ex) for ex in sorted(exons_se_i)])
        )
    return tx_info
