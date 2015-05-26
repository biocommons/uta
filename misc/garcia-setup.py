from uta.db.transcriptdb import TranscriptDB
from uta.exceptions import *
from uta.tools.transcriptmapper import TranscriptMapper

import csv
import hgvs.parser
import prettytable

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
    tests_in = csv.DictReader(open(tests_fn, 'r'), delimiter='\t')

    results_table = prettytable.PrettyTable(
        field_names=['I', '=', 'S', 'gene', 'hgvsc', 'c0', 'g0', 'g1', 'hgvsg', 'gpos'])
    for test_rec in tests_in:
        if test_rec['Gene'].startswith('#'):
            continue
        g_hgvs = test_rec['Genomic_position']
        g_var = hgvs_parser.parse(g_hgvs)
        g_pos = (g_var.pos.start, g_var.pos.end)
        for c_hgvs in [test_rec['Mapping1'], test_rec['Mapping2']]:
            c_var = hgvs_parser.parse(c_hgvs)
            if c_var.seqref not in tm_cache:
                try:
                    tm_cache[c_var.seqref] = TranscriptMapper(
                        db, ref=ref, ac=c_var.seqref)
                except UTAError as e:
                    print(e.message)
                    continue
            tm = tm_cache[c_var.seqref]
            intronic = c_var.pos.start.is_intronic or c_var.pos.end.is_intronic
            c0 = (c_var.pos.start.base - 1, c_var.pos.end.base)
            g0 = tm.c_to_g(*c0)
            g1 = (g0[0] + 1, g0[1])
            results_table.add_row([str(intronic)[0], str(g_pos == g1)[0],
                                   tm.tx_info['gene'], tm.tx_info['strand'],
                                   c_hgvs, c0, g0, g1,
                                   g_hgvs, g_pos])
            if intronic:
                break
    return results_table

# <LICENSE>
# Copyright 2014 UTA Contributors (https://bitbucket.org/biocommons/uta)
##
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
##
# http://www.apache.org/licenses/LICENSE-2.0
##
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# </LICENSE>
