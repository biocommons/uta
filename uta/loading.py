from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import datetime
import gzip
import itertools
import logging
import time

from bioutils.coordinates import strand_pm_to_int, MINUS_STRAND
from sqlalchemy.orm.exc import NoResultFound;

import uta
import uta.formats.exonset as ufes
import uta.formats.geneinfo as ufgi
import uta.formats.seqinfo as ufsi
import uta.formats.txinfo as ufti

usam = uta.models                         # backward compatibility

logger = logging.getLogger(__name__)

#TODO: Schema qualify all queries/remove set search_path

def drop_schema(session, opts, cf):
    if session.bind.name == "postgresql" and usam.use_schema:
        session.execute(
            "set role {admin_role};".format(admin_role=cf.get("uta", "admin_role")))
        session.execute("set search_path = " + usam.schema_name)

        ddl = "drop schema if exists " + usam.schema_name + " cascade"
        session.execute(ddl)
        session.commit()
        logger.info(ddl)


def create_schema(session, opts, cf):
    """Create and populate initial schema"""
    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    if session.bind.name == "postgresql" and usam.use_schema:
        session.execute("create schema " + usam.schema_name)
        session.execute("set search_path = " + usam.schema_name)
        session.commit()

    usam.Base.metadata.create_all(session.bind)
    session.add(usam.Meta(key="schema_version", value=usam.schema_version))
    session.add(
        usam.Meta(key="created", value=datetime.datetime.now().isoformat()))
    session.add(usam.Meta(
        key="license", value="CC-BY-SA (http://creativecommons.org/licenses/by-sa/4.0/deed.en_US"))
    session.commit()
    logger.info("created schema")


def load_sql(session, opts, cf):
    """Create views"""
    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    for fn in opts["FILES"]:
        logger.info("loading " + fn)
        session.execute(open(fn).read())
    session.commit()


def load_origin(session, opts, cf):
    """Add/merge data origins

    """

    def _none_if_empty(s):
        return None if s == "" else s

    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    orir = csv.DictReader(open(opts["FILE"]), delimiter=b'\t')
    for rec in orir:
        ori = usam.Origin(name=rec["name"],
                          descr=_none_if_empty(rec["descr"]),
                          url=_none_if_empty(rec["url"]),
                          url_ac_fmt=_none_if_empty(rec["url_ac_fmt"]),
                          )
        u_ori = session.query(usam.Origin).filter(
            usam.Origin.name == rec["name"]).first()
        if u_ori:
            ori.origin_id = u_ori.origin_id
            session.merge(ori)
        else:
            session.add(ori)
        logger.info("Merged {ori.name} ({ori.descr})".format(ori=ori))
    session.commit()



def load_seqinfo(session, opts, cf):
    """load Seq entries with accessions from fasta file
    """

    # TODO: load_seqinfo is horrifically slow. There must be a better way.
    # To try:
    # - fetch all md5,alias pairs as multimap
    # - loop over input (as-is); for each md5,alias pair:
    # - if md5 not in multimap, add seq_id
    # - if anno for md5 not in multimap, add anno
    # -    .. else: update description if necessary
    
    update_period = 100

    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    n_rows = len(gzip.open(opts["FILE"]).readlines()) - 1

    sir = ufsi.SeqInfoReader(gzip.open(opts["FILE"]))
    logger.info("opened " + opts["FILE"])

    i_md5 = 0
    for md5, si_iter in itertools.groupby(sorted(sir, key=lambda si: si.md5),
                                          key=lambda si: si.md5):
        sis = list(si_iter)
        si = sis[0]

        i_md5 += 1
        if i_md5 % update_period == 1:
            logger.info("{i_md5}/{n_rows} {p:.1f}%: updated/added seq {md5} with {n} acs ({acs})".format(
                i_md5=i_md5, n_rows=n_rows, md5=md5, p=(i_md5 + 1) / n_rows * 100,
                n=len(sis), acs=",".join(si.ac for si in sis)))

        u_seq = session.query(usam.Seq).filter(usam.Seq.seq_id == md5).first()
        if u_seq is None:
            # if the seq doesn't exist, we can add it and the sequence
            # annotations without fear of collision (which is faster)
            u_seq = usam.Seq(seq_id=md5, len=si.len, seq=si.seq)
            session.add(u_seq)

            for si in sis:
                try:
                    u_ori = session.query(usam.Origin).filter(
                        usam.Origin.name == si.origin).one()
                except NoResultFound as e:
                    logger.error("No origin for "+si.origin)
                    raise e
                u_seqanno = usam.SeqAnno(origin_id=u_ori.origin_id, seq_id=si.md5,
                                         ac=si.ac, descr=si.descr)
                session.add(u_seqanno)

            session.commit()

        else:
            # the seq existed, and therefore some of the incoming annotations may
            # exist. Need to check first.
            for si in sis:
                u_ori = session.query(usam.Origin).filter(
                    usam.Origin.name == si.origin).one()
                u_seqanno = session.query(usam.SeqAnno).filter(
                    usam.SeqAnno.origin_id == u_ori.origin_id,
                    usam.SeqAnno.seq_id == si.md5,
                    usam.SeqAnno.ac == si.ac).first()
                if u_seqanno:
                    # update descr, perhaps
                    if si.descr and u_seqanno.descr != si.descr:
                        u_seqanno.descr = si.descr
                        session.merge(u_seqanno)
                        logger.info("updated description for " + si.ac)
                else:
                    # create the new descr
                    u_seqanno = usam.SeqAnno(origin_id=u_ori.origin_id, seq_id=si.md5,
                                             ac=si.ac, descr=si.descr)
                    session.add(u_seqanno)

            session.commit()
            logger.debug("updated annotations for seq {md5} with {n} acs ({acs})".format(
                md5=md5, n=len(sis), acs=",".join(si.ac for si in sis)))


def load_exonset(session, opts, cf):
    # exonsets and associated exons are loaded together

    update_period = 50 

    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    known_tx = set([u_tx.ac
                    for u_tx in session.query(usam.Transcript)])

    known_es = set([(u_es.tx_ac, u_es.alt_ac, u_es.alt_aln_method)
                    for u_es in session.query(usam.ExonSet)])
    logger.info("{n} known exon_set keys; will skip those during loading".format(
        n=len(known_es)))

    n_rows = len(gzip.open(opts["FILE"]).readlines()) - 1
    esr = ufes.ExonSetReader(gzip.open(opts["FILE"]))
    logger.info("opened " + opts["FILE"])

    for i_es, es in enumerate(esr):
        key = (es.tx_ac, es.alt_ac, es.method)
    
        if es.tx_ac not in known_tx:
            # catch cases where UCSC has refseq transcripts not in UTA
            # Known causes:
            # - collecting UCSC data after NCBI data, and new refseq created
            # - refseq fails alignment criteria (see data/ncbi/ncbi-parse-gff.log)
            logger.warn("Could not load exon set: unknown transcript {es.tx_ac} in {key}".format(
                es=es, key=key))
            continue

        if i_es % update_period == 0 or i_es + 1 == n_rows:
            logger.info("{i_es}/{n_rows} {p:.1f}%: loading exonset  ({key})".format(
                i_es=i_es, n_rows=n_rows, p=(i_es + 1) / n_rows * 100, key=str(key)))

        if key in known_es:
            continue
        known_es.add(key)

        u_es = usam.ExonSet(
            tx_ac=es.tx_ac,
            alt_ac=es.alt_ac,
            alt_aln_method=es.method,
            alt_strand=es.strand
        )
        session.add(u_es)

        exons = [map(int, ex.split(",")) for ex in es.exons_se_i.split(";")]
        exons.sort(reverse=int(es.strand) == MINUS_STRAND)
        for i_ex, ex in enumerate(exons):
            s, e = ex
            u_ex = usam.Exon(
                exon_set=u_es,
                start_i=s,
                end_i=e,
                ord=i_ex,
            )
            session.add(u_ex)

        session.commit()


def load_geneinfo(session, opts, cf):
    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    gir = ufgi.GeneInfoReader(gzip.open(opts["FILE"]))
    logger.info("opened " + opts["FILE"])

    for i_gi, gi in enumerate(gir):
        session.merge(
            usam.Gene(
                hgnc=gi.hgnc,
                maploc=gi.maploc,
                descr=gi.descr,
                summary=gi.summary,
                aliases=gi.aliases,
            ))
        logger.info("Added {gi.hgnc} ({gi.summary})".format(gi=gi))
    session.commit()


def load_txinfo(session, opts, cf):
    # TODO: add cds_md5 column and load here
    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    self_aln_method = "transcript"
    update_period = 250

    from bioutils.digests import seq_md5
    from multifastadb import MultiFastaDB

    fa_dirs = cf.get("sequences", "fasta_directories").strip().splitlines()
    mfdb = MultiFastaDB(fa_dirs, use_meta_index=True)
    logger.info("Opened sequence directories: " + ",".join(fa_dirs))

    known_acs = set([u_ti.ac for u_ti in session.query(usam.Transcript)])
    n_rows = len(gzip.open(opts["FILE"]).readlines()) - 1
    tir = ufti.TxInfoReader(gzip.open(opts["FILE"]))
    logger.info("opened " + opts["FILE"])

    for i_ti, ti in enumerate(tir):
        if i_ti % update_period == 0 or i_ti + 1 == n_rows:
            logger.info("{i_ti}/{n_rows} {p:.1f}%: loading transcript {ac}".format(
                i_ti=i_ti, n_rows=n_rows, p=(i_ti + 1) / n_rows * 100, ac=ti.ac))

        if ti.ac in known_acs:
            logger.warning("skipping new definition of transcript " + ti.ac)
            continue
        known_acs.add(ti.ac)

        if ti.exons_se_i == "":
            logger.warning(ti.ac + ": no exons?!; skipping.")
            continue

        try:
            ori = session.query(usam.Origin).filter(
                usam.Origin.name == ti.origin).one()
        except NoResultFound as e:
            logger.error("No origin for " + ti.origin)
            raise e

        if ti.cds_se_i:
            cds_start_i, cds_end_i = map(int, ti.cds_se_i.split(","))
        else:
            cds_start_i = cds_end_i = None

        try:
            cds_seq = mfdb.fetch(ti.ac, cds_start_i, cds_end_i)
        except KeyError:
            #raise Exception("{ac}: not in sequence database; skipping".format(
            #    ac=ti.ac))
            logger.error("{ac}: not in sequence database; skipping".format(
                ac=ti.ac))
            continue

        cds_md5 = seq_md5(cds_seq)

        u_tx = usam.Transcript(
            ac=ti.ac,
            origin=ori,
            hgnc=ti.hgnc,
            cds_start_i=cds_start_i,
            cds_end_i=cds_end_i,
            cds_md5=cds_md5,
        )
        session.add(u_tx)

        u_es = usam.ExonSet(
            transcript=u_tx,
            alt_ac=ti.ac,
            alt_strand=1,
            alt_aln_method=self_aln_method,
        )
        session.add(u_es)

        exons = [map(int, ex.split(",")) for ex in ti.exons_se_i.split(";")]
        for i_ex, ex in enumerate(exons):
            s, e = ex
            u_ex = usam.Exon(
                exon_set=u_es,
                start_i=s,
                end_i=e,
                ord=i_ex,
            )
            session.add(u_ex)

        session.commit()


def align_exons(session, opts, cf):
    # N.B. setup.py declares dependencies for using uta as a client.  The
    # imports below are loading depenencies only and are not in setup.py.

    import psycopg2.extras
    from bioutils.sequences import reverse_complement
    from multifastadb import MultiFastaDB
    import uta_align.align.algorithms as utaaa

    update_period = 1000

    def _get_cursor(con):
        cur = con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        cur.execute("set role {admin_role};".format(
            admin_role=cf.get("uta", "admin_role")))
        cur.execute("set search_path = " + usam.schema_name)
        return cur

    def align(s1, s2):
        score, cigar = utaaa.needleman_wunsch_gotoh_align(str(s1),
                                                          str(s2),
                                                          extended_cigar=True)
        tx_aseq, alt_aseq = utaaa.cigar_alignment(
            tx_seq, alt_seq, cigar, hide_match=False)
        return tx_aseq, alt_aseq, cigar.to_string()

    aln_sel_sql = """
    SELECT * FROM tx_alt_exon_pairs_v TAEP
    WHERE exon_aln_id is NULL
    ORDER BY hgnc
    """

    aln_ins_sql = """
    INSERT INTO exon_aln (tx_exon_id,alt_exon_id,cigar,added,tx_aseq,alt_aseq) VALUES (%s,%s,%s,%s,%s,%s)
    """

    con = session.bind.pool.connect()
    cur = _get_cursor(con)
    cur.execute(aln_sel_sql)
    n_rows = cur.rowcount

    if n_rows == 0:
        return

    fa_dirs = cf.get("sequences", "fasta_directories").strip().splitlines()
    mfdb = MultiFastaDB(fa_dirs, use_meta_index=True)
    logger.info("Opened sequence directories: " + ",".join(fa_dirs))

    rows = cur.fetchall()
    ac_warning = set()
    tx_acs = set()
    aln_rate_s = None
    decay_rate = 0.25
    n0, t0 = 0, time.time()

    for i_r, r in enumerate(rows):
        if r.tx_ac in ac_warning or r.alt_ac in ac_warning:
            continue
        try:
            tx_seq = mfdb.fetch(r.tx_ac, r.tx_start_i, r.tx_end_i)
        except KeyError:
            logger.warning(
                "{r.tx_ac}: Not in sequence sources; can't align".format(r=r))
            ac_warning.add(r.tx_ac)
            continue
        try:
            alt_seq = mfdb.fetch(r.alt_ac, r.alt_start_i, r.alt_end_i)
        except KeyError:
            logger.warning(
                "{r.alt_ac}: Not in sequence sources; can't align".format(r=r))
            ac_warning.add(r.alt_ac)
            continue

        if r.alt_strand == MINUS_STRAND:
            alt_seq = reverse_complement(alt_seq)
        tx_seq = tx_seq.upper()
        alt_seq = alt_seq.upper()

        tx_aseq, alt_aseq, cigar_str = align(tx_seq, alt_seq)

        added = datetime.datetime.now()
        cur.execute(aln_ins_sql, [r.tx_exon_id, r.alt_exon_id, cigar_str, added, tx_aseq, alt_aseq])
        tx_acs.add(r.tx_ac)

        if i_r > 0 and (i_r % update_period == 0 or (i_r + 1) == n_rows):
            con.commit()
            n1, t1 = i_r, time.time()
            nd, td = n1 - n0, t1 - t0
            aln_rate = nd / td      # aln rate on this update period
            if aln_rate_s is None:  # aln_rate_s is EWMA smoothed average
                aln_rate_s = aln_rate
            else:
                aln_rate_s = decay_rate * aln_rate + (1.0 - decay_rate) * aln_rate_s
            etr = (n_rows - i_r - 1) / aln_rate_s        # etr in secs
            etr_s = str(datetime.timedelta(seconds=round(etr)))  # etr as H:M:S
            logger.info("{i_r}/{n_rows} {p_r:.1f}%; committed; speed={speed:.1f}/{speed_s:.1f} aln/sec (inst/emwa); etr={etr:.0f}s ({etr_s}); {n_tx} tx".format(
                i_r=i_r, n_rows=n_rows, p_r=i_r / n_rows * 100, speed=aln_rate, speed_s=aln_rate_s, etr=etr,
                etr_s=etr_s, n_tx=len(tx_acs)))
            tx_acs = set()
            n0, t0 = n1, t1

    cur.close()
    con.close()


def load_ncbi_geneinfo(session, opts, cf):
    """
    import data as downloaded (by you) from 
    ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz
    """
    import uta.parsers.geneinfo

    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    gip = uta.parsers.geneinfo.GeneInfoParser(gzip.open(opts["FILE"]))
    for gi in gip:
        if gi["tax_id"] != "9606" or gi["Symbol_from_nomenclature_authority"] == "-":
            continue
        g = usam.Gene(
            gene_id=gi["GeneID"],
            hgnc=gi["Symbol_from_nomenclature_authority"],
            maploc=gi["map_location"],
            descr=gi["Full_name_from_nomenclature_authority"],
            aliases=gi["Synonyms"],
            strand=gi[""],
        )
        session.add(g)
        logger.info("loaded gene {g.hgnc} ({g.descr})".format(g=g))
    session.commit()


def load_sequences(session, opts, cf):
    from multifastadb import MultiFastaDB

    # TODO: Don't store sequences in UTA
    # load sequences up to max_len in size
    # 2e6 was chosen empirically based on sizes of NMs, NGs, NWs, NTs, NCs
    max_len = int(2e6)

    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    fa_dirs = cf.get("sequences", "fasta_directories").strip().splitlines()
    mfdb = MultiFastaDB(fa_dirs, use_meta_index=True)
    logger.info("Opened sequence directories: " + ",".join(fa_dirs))

    # fetch accessions for given sequences
    sql = """
    select S.seq_id,S.len,array_agg(SA.ac order by SA.ac~'^ENST',SA.ac) as acs
    from seq S
    join seq_anno SA on S.seq_id=SA.seq_id
    where S.len <= {max_len} and S.seq is NULL
    group by S.seq_id,len
    """.format(max_len=max_len)

    def _fetch_first(acs):
        # try all accessions in acs, return sequence of first that returns a
        # sequence
        for ac in row["acs"]:
            try:
                return mfdb.fetch(ac)
            except KeyError:
                pass
        return None

    for row in session.execute(sql):
        seq = _fetch_first(row["acs"])
        if seq is None:
            logger.warn("No sequence found for {acs}".format(acs=row["acs"]))
            continue
        seq = seq.upper()
        if row["len"] != len(seq):
            logger.error("Expected a sequence of length {len} for {md5} ({acs}); got sequence of length {len2}".format(
                len=row["len"], md5=row["seq_id"], acs=row["acs"], len2=len(seq)))
            continue
        assert row["len"] == len(seq), "expected a sequence of length {len} for {md5} ({acs}); got length {len2}".format(
            len=row["len"], md5=row["seq_id"], acs=row["acs"], len2=len(seq))
        session.execute(usam.Seq.__table__.update().values(
            seq=seq).where(usam.Seq.seq_id == row["seq_id"]))
        logger.info("loaded sequence of length {len} for {md5} ({acs})".format(
            len=len(seq), md5=row["seq_id"], acs=row["acs"]))
        session.commit()


def load_ncbi_seqgene(session, opts, cf):
    """
    import data as downloaded (by you) as from
    ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/seq_gene.md.gz
    """
    def _seqgene_recs_to_tx_info(ac, assy, recs):
        ti = {
            "ac": ac,
            "assy": assy,
            "strand": strand_pm_to_int(recs[0]["chr_orient"]),
            "gene_id": int(recs[0]["feature_id"].replace("GeneID:", "")) if "GeneID" in recs[0]["feature_id"] else None,
        }
        segs = [(r["feature_type"], int(r["chr_start"]) - 1, int(r["chr_stop"]))
                for r in recs]
        cds_seg_idxs = [i for i in range(len(segs)) if segs[i][0] == "CDS"]
        # merge UTR-CDS and CDS-UTR exons if end of first == start of second
        # prefer this over general adjacent exon merge in case of alignment artifacts
        # last exon
        ei = cds_seg_idxs[-1]
        ti["cds_end_i"] = segs[ei][2]
        if ei < len(segs) - 1:
            if segs[ei][2] == segs[ei + 1][1]:
                segs[ei:ei + 2] = [("M", segs[ei][1], segs[ei + 1][2])]
        # first exon
        ei = cds_seg_idxs[0]
        ti["cds_start_i"] = segs[ei][1]
        if ei > 0:
            if segs[ei - 1][2] == segs[ei][1]:
                segs[ei - 1:ei + 1] = [("M", segs[ei - 1][1], segs[ei][2])]
        ti["exon_se_i"] = [s[1:3] for s in segs]
        return ti

    import uta.parsers.seqgene

    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    o_refseq = session.query(usam.Origin).filter(
        usam.Origin.name == "NCBI RefSeq").one()

    sg_filter = lambda r: (r["transcript"].startswith("NM_")
                           and r["group_label"] == "GRCh37.p10-Primary Assembly"
                           and r["feature_type"] in ["CDS", "UTR"])
    sgparser = uta.parsers.seqgene.SeqGeneParser(gzip.open(opts["FILE"]),
                                                 filter=sg_filter)
    slurp = sorted(list(sgparser),
                   key=lambda r: (r["transcript"], r["group_label"], r["chr_start"], r["chr_stop"]))
    for k, i in itertools.groupby(slurp, key=lambda r: (r["transcript"], r["group_label"])):
        ac, assy = k
        ti = _seqgene_recs_to_tx_info(ac, assy, list(i))

        resp = session.query(usam.Transcript).filter(usam.Transcript.ac == ac)
        if resp.count() == 0:
            t = usam.Transcript(ac=ac, origin=o_refseq, gene_id=ti["gene_id"])
            session.add(t)
        else:
            t = resp.one()

        es = usam.ExonSet(
            transcript_id=t.transcript_id,
            ref_nseq_id=99,
            strand=ti["strand"],
            cds_start_i=ti["cds_start_i"],
            cds_end_i=ti["cds_end_i"],
        )


def grant_permissions(session, opts, cf):
    schema = usam.schema_name

    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    cmds = [
        # alter db doesn't belong here, and probably better to avoid the implicit behevior this encourages
        # "alter database {db} set search_path = {schema}".format(db=cf.get("uta", "database"),schema=schema),
        "grant usage on schema " + schema + " to PUBLIC",
    ]

    sql = "select concat(schemaname,'.',tablename) as fqrn from pg_tables where schemaname='{schema}'".format(
        schema=schema)
    rows = list(session.execute(sql))
    cmds += ["grant select on {fqrn} to PUBLIC".format(
        fqrn=row["fqrn"]) for row in rows]
    cmds += ["alter table {fqrn} owner to uta_admin".format(
        fqrn=row["fqrn"]) for row in rows]

    sql = "select concat(schemaname,'.',viewname) as fqrn from pg_views where schemaname='{schema}'".format(
        schema=schema)
    rows = list(session.execute(sql))
    cmds += ["grant select on {fqrn} to PUBLIC".format(
        fqrn=row["fqrn"]) for row in rows]
    cmds += ["alter view {fqrn} owner to uta_admin".format(
        fqrn=row["fqrn"]) for row in rows]

    sql = "select concat(schemaname,'.',matviewname) as fqrn from pg_matviews where schemaname='{schema}'".format(
        schema=schema)
    rows = list(session.execute(sql))
    cmds += ["grant select on {fqrn} to PUBLIC".format(
        fqrn=row["fqrn"]) for row in rows]
    cmds += ["alter materialized view {fqrn} owner to uta_admin".format(
        fqrn=row["fqrn"]) for row in rows]

    for cmd in sorted(cmds):
        logger.info(cmd)
        session.execute(cmd)
    session.commit()


def refresh_matviews(session, opts, cf):
    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)

    # matviews must be updated in dependency order. Unfortunately,
    # it's difficult to determine this programmatically. The "right"
    # solution is a recursive CTE, but I was unable to find or write
    # one readily. This function should be consdered a placeholder for
    # the right way to update, which doesn't exist yet.

    # TODO: Determine mv refresh order programmatically.
    # sql = "select concat(schemaname,".",matviewname) as fqrn from pg_matviews where schemaname="{schema}"".format(
    #     schema=schema)
    # rows = list(session.execute(sql))
    # cmds = [ "refresh materialized view {fqrn}".format(fqrn=row["fqrn"]) for row in rows ]

    cmds = [
        # N.B. Order matters!
        "refresh materialized view exon_set_exons_fp_mv",
        "refresh materialized view tx_exon_set_summary_mv",
        "refresh materialized view tx_def_summary_mv",
        # "refresh materialized view tx_aln_cigar_mv",
        # "refresh materialized view tx_aln_summary_mv",
    ]

    for cmd in cmds:
        logger.info(cmd)
        session.execute(cmd)
    session.commit()


def analyze(session, opts, cf):
    session.execute("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role")))
    session.execute("set search_path = " + usam.schema_name)
    cmds = [
        "analyze verbose"
    ]
    for cmd in cmds:
        logger.info(cmd)
        session.execute(cmd)
    session.commit()


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
