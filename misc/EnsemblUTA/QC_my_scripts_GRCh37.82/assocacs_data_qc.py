# -*- coding: utf-8 -*-

"""
Script that compares the output of the CAUSEYFREEMAN Ensembl fetch data (query) with the data derived from
https://github.com/biocommons/uta/blob/master/sbin/ensembl-fetch (reference)

The script collects the data from the reference and the query and the reference files and create a dictionary using the
Ensembl transcript identifier as the key. Note, the identifier lacks the version number when created by the original
.pl script, so the dictionaries generated from the query data must be adapted to match


Workflow
assocacs data structure
hgnc	    tx_ac	        pro_ac	        origin
LINC00632	ENST00000607004	ENSP00000476053	ensembl-90


Intended dictionary structure
{ 'ENST00000607004':
    [LINC00632,	ENSP00000476053, ensembl-90]
}
"""

# import modules
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
QUERY = os.path.join(ROOT, 'query_data')
REFERENCE = os.path.join(ROOT, 'reference_data')
RESULTS = os.path.join(ROOT, 'results')

# Open and read data
query_file = os.path.join(QUERY, 'assocacs')
reference_file = os.path.join(REFERENCE, 'assocacs_90')
query_handle = open(query_file)
reference_handle = open(reference_file)
query_data = query_handle.read()
query_handle.close()
reference_data = reference_handle.read()
reference_handle.close()

# Create empty data dictionaries
query_dict = {}
reference_dict = {}

# Fill the reference dictionary
reference_list = reference_data.split('\n')
for ref_set in reference_list:
    if re.match('#', ref_set):
        continue
    else:
        try:
            ref_set = ref_set.split('\t')
            reference_dict[ref_set[1]] = [ref_set[0]] + ref_set[2:-1] + ['ensembl-82']
        except IndexError:
            continue

# Fill the query dictionary
query_list = query_data.split('\n')
for que_set in query_list:
    if re.match('#', que_set):
        continue
    else:
        try:
            que_set = que_set.split('\t')
            query_dict[que_set[1]] = [que_set[0]] + [que_set[2]] + [que_set[3]]
        except IndexError:
            continue

# Compare the data
pass_count = 0
fail_count = 0
epic_fails = []
epic_passes = []
for id, data in reference_dict.iteritems():
    # The query data is limited to GENCODE basic, so some records in the reference will be absent from the query
    try:
        if data == query_dict[id]:
            pass_count = pass_count + 1
            epic_pass = [id] + data
            epic_passes.append(epic_pass)
        else:
            fail_count = fail_count + 1
            epic_fail = [id] + data
            epic_fails.append(epic_fail)
            epic_contrast = [id] + query_dict[id]
            epic_fails.append(epic_contrast)
    except KeyError:
        continue

# Write out summary results
result_summary = 'Results summary\n%s query records match the reference dataset\n%s query ' \
    'records do not match the reference dataset\n%s records in total were compared\n%s records were in the ref data set\n%s records were in the query data set\n\n' % (str(pass_count),
                                                                                                                                                                       str(fail_count),
                                                                                                                                                                       str(pass_count +
                                                                                                                                                                           fail_count),
                                                                                                                                                                       str(len(reference_dict.keys())),
                                                                                                                                                                       str(len(query_dict.keys()))                                                                                                                                )
# Write results data
fails_handle = os.path.join(RESULTS, 'assocacs_fail.txt')
fail_me = open(fails_handle, 'w')
passes_handle = os.path.join(RESULTS, 'assocacs_pass.txt')
pass_me = open(passes_handle, 'w')
pass_me.write(result_summary)
for fails in epic_fails:
    fl = '\t'.join(fails)
    fl = fl + '\n'
    fail_me.write(fl)
fail_me.close()
for passes in epic_passes:
    ps = '\t'.join(passes)
    ps = ps + '\n'
    pass_me.write(ps)
pass_me.close()
