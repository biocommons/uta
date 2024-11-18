import argparse
import logging

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

import uta
from uta.models import Gene, Transcript
from uta.tools.file_utils import open_file


logger = None
n = 50000


def backfill_gene(uta_session: Session, gene_update_file: str) -> None:
    logger.info("Dropping gene table contents")
    uta_session.execute(text("DELETE FROM uta.gene;"))
    uta_session.commit()

    logger.info(f"Back filling gene table from {gene_update_file}")
    now_ts = datetime.now()
    i = 0
    new_genes = []
    with open_file(gene_update_file) as f:
        for line in f:
            if line.startswith("gene_id"):
                continue

            if i % n == 0:
                if i > 0:
                    logger.info(f"Bulk inserting {len(new_genes)} genes")
                    uta_session.bulk_save_objects(new_genes)
                    uta_session.commit()
                logger.info(f"Processing chunk {int(i/n) + 1}")
                new_genes = []

            gene_id, hgnc, maploc, desc, summary, aliases, added = line.rstrip("\r\n").split("\t")
            # set timestamp from file string, if empty set to now.
            if added == "":
                added_ts = now_ts
            else:
                added_ts = datetime.strptime(added, "%Y-%m-%d %H:%M:%S.%f")

            # clean up aliases
            aliases = aliases.replace("{", "").replace("}", "")
            if aliases == "-":
                aliases = None

            gene = Gene(
                gene_id=gene_id,
                hgnc=hgnc,
                maploc=maploc if maploc else None,
                descr=desc if desc else None,
                summary=summary if desc else None,
                aliases=aliases if aliases else None,
                added=added_ts,
            )
            i += 1
            new_genes.append(gene)

    logger.info(f"Bulk inserting {len(new_genes)} genes")
    uta_session.bulk_save_objects(new_genes)
    uta_session.commit()
    logger.info(f"Inserted {i} total genes")


def backfill_transcript(uta_session: Session, transcript_update_file: str) -> None:
    logger.info("Backfilling gene_id in transcript table")
    tx_ac_to_gene_id = {}

    logger.info(f"Reading transcript to gene id mappings from {transcript_update_file}")
    with open_file(transcript_update_file) as f:
        for line in f:
            if line.startswith("origin"):
                continue
            _, tx_ac, gene_id, _ = line.rstrip("\r\n").split("\t")
            tx_ac_to_gene_id[tx_ac] = gene_id
    logger.info(f"  - {len(tx_ac_to_gene_id)} mappings read")

    i = 0
    txs = []
    for tx_ac, gene_id in tx_ac_to_gene_id.items():
        if i % n == 0:
            if i > 0:
                logger.info(f"Updating {len(txs)} transcripts")
                uta_session.flush()

            logger.info(f"Processing chunk {int(i/n) + 1}")
            txs = []

        tx = uta_session.query(Transcript).filter(Transcript.ac == tx_ac).one()
        tx.gene_id = gene_id
        txs.append(tx)
        i += 1

    logger.info(f"Updating {len(txs)} transcripts")
    uta_session.flush()
    uta_session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill gene_id in gene and transcript tables")
    parser.add_argument("db_url", help="URL of the UTA database")
    parser.add_argument("gene_update_file", type=str, help="File containing gene_id updates for gene table")
    parser.add_argument("transcript_update_file", type=str, help="File containing gene_id updates for transcript table")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logger = logging.getLogger("backfill_gene_id")

    session = uta.connect(args.db_url)

    backfill_gene(session, args.gene_update_file)
    backfill_transcript(session, args.transcript_update_file)
    session.close()
