from uta.db.transcriptdb import TranscriptDB
from uta.exceptions import *
from uta.tools.transcriptmapper import TranscriptMapper

import csv, hgvs.parser, prettytable

ref = 'GRCh37.p10'
tests_fn = 'tests/data/garcia.tsv'


#test_rec = tests_in.next()
#g_var = hgvs_parser.parse(test_rec['Genomic_position'])
#c_hgvs = test_rec['Mapping1']
#c_var = hgvs_parser.parse(c_hgvs)
#tm = TranscriptMapper(db, ref = ref, ac = c_var.seqref)


tm_cache = dict()


def mk_results_table(fn):
    db = TranscriptDB()

    hgvs_parser = hgvs.parser.Parser()
    tests_in = csv.DictReader(open(tests_fn,'r'),delimiter='\t')

    results_table = prettytable.PrettyTable(field_names = ['hgvsg','gpos','hgvsc','c0','g0','g1','match?'])
    for test_rec in tests_in:
        if test_rec['Gene'].startswith('#'):
            continue
        g_hgvs = test_rec['Genomic_position']
        g_var = hgvs_parser.parse(g_hgvs)
        g_pos = (g_var.pos.start,g_var.pos.end)
        for c_hgvs in [test_rec['Mapping1'], test_rec['Mapping2']]:
            c_var = hgvs_parser.parse(c_hgvs)
            if c_var.pos.start.offset != 0 or c_var.pos.end.offset != 0:
                print(c_hgvs + ": skipping intronic variant")
                continue
            try:
                if c_var.seqref not in tm_cache:
                    tm_cache[c_var.seqref] = TranscriptMapper(db, ref = ref, ac = c_var.seqref)
                tm = tm_cache[c_var.seqref]
                c0 = (c_var.pos.start.base - 1, c_var.pos.end.base)
                g0 = tm.c_to_g(*c0)
                g1 = (g0[0]+1,g0[1])
                results_table.add_row([ g_hgvs, g_pos,
                                        c_hgvs, c0, g0, g1,
                                        g_pos == g1 ])
            except UTAError as e:
                print(e.message)
    return results_table
