#!/usr/bin/env python

import argparse
import csv
import logging.config
import sys

import importlib_resources

from uta.formats.exonset import ExonSetReader, ExonSetWriter
from uta.formats.txinfo import TxInfoReader
from uta.tools.file_utils import open_file

logging_conf_fn = importlib_resources.files("uta").joinpath("etc/logging.conf")
logging.config.fileConfig(logging_conf_fn)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def filter_exonset(exonset_file, transcript_ids, missing_ids_file):
    with open_file(exonset_file) as es_f, open(missing_ids_file, 'w') as missing_f:
        exonsets = ExonSetReader(es_f)
        esw = ExonSetWriter(sys.stdout)
        writer_missing = csv.writer(missing_f)
        missing_acs = set()

        for exonset in exonsets:
            if exonset.tx_ac in transcript_ids:
                esw.write(exonset)
            else:
                logger.warning(f"Exon set transcript {exonset.tx_ac} not found in txinfo file. Filtering out.")
                writer_missing.writerow([exonset.tx_ac])
                missing_acs.add(exonset.tx_ac)
    logger.info(f"Filtered out exon sets for {len(missing_acs)} transcript(s): {','.join(missing_acs)}")


def main():
    parser = argparse.ArgumentParser(description='Filter exonset data.')
    parser.add_argument('--tx-info', help='Path to the transcript info file')
    parser.add_argument('--exonsets', help='Path to the exonset file')
    parser.add_argument('--missing-ids', help='Path to the missing transcript ids file')
    args = parser.parse_args()

    with open_file(args.tx_info) as f:
        tx_reader = TxInfoReader(f)
        transcript_ids = {row.ac for row in tx_reader}
    filter_exonset(args.exonsets, transcript_ids, args.missing_ids)


if __name__ == '__main__':
    main()
