#!/usr/bin/env python

"""CORE-187 suggested that we were missing a transcript,
ENST00000576892, for FAM58A. This script demonstrates the cause: that
transcript is on a patch region.

"""


import logging
import sys
 
import requests

logger = logging.getLogger(__name__)

base_uri = "http://grch37.rest.ensembl.org"

def _fetch_json(path):
    uri = base_uri + path
    r = requests.get(uri, headers={"Content-Type" : "application/json"})
    r.raise_for_status()
    logger.info('fetched '+uri)
    return r.json()

def fetch_gene(hgnc):
    return _fetch_json("/xrefs/symbol/homo_sapiens/"+hgnc)

def lookup(id):
    return _fetch_json("/lookup/id/{id}?expand=1".format(id=id))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    ensgs = [r['id'] for r in fetch_gene('FAM58A') if r['id'].startswith("ENSG")]

    for ensg in ensgs:
        l = lookup(ensg)
        txs = l['Transcript']
        print("* {l[display_name]} {l[version]} {l[seq_region_name]} {l[object_type]}; {n} transcripts ".format(l=l, n=len(txs)))
        for tx in txs:
            print("  {tx[display_name]} {tx[id]} {tx[version]} {tx[seq_region_name]}; {n} exons".format(tx=tx, n=len(tx)))
