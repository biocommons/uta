"""Schema for Universal Transcript Archive
"""

import datetime
import hashlib

import sqlalchemy as sa
import sqlalchemy.orm as sao
import sqlalchemy.types
import sqlalchemy.sql.functions
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql


############################################################################
# schema name support
# also see etc/uta.conf

schema_version = "1.1"
use_schema = True
if use_schema:
    schema_name = "uta"
else:
    schema_name = None


############################################################################

Base = declarative_base(
    metadata=sa.MetaData(schema=schema_name)
)

class Meta(Base):
    __tablename__ = "meta"
    key = sa.Column(sa.Text, primary_key=True, nullable=False)
    value = sa.Column(sa.Text, nullable=False)


class Origin(Base):
    __tablename__ = "origin"

    # columns:
    origin_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.Text, nullable=False, unique=True)
    descr = sa.Column(sa.Text)
    updated = sa.Column(
        sa.DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    url = sa.Column(sa.Text, nullable=True)
    url_ac_fmt = sa.Column(sa.Text, nullable=True)

    # methods:
    def tickle_update(self):
        self.updated = datetime.datetime.now()


class Seq(Base):
    __tablename__ = "seq"

    def _seq_hash(context):
        seq = context.current_parameters["seq"]
        return None if seq is None else hashlib.md5(seq.upper().encode("ascii")).hexdigest()

    def _seq_len(context):
        seq = context.current_parameters["seq"]
        return None if seq is None else len(seq)

    # columns:
    seq_id = sa.Column(sa.Text, primary_key=True, default=_seq_hash)
    len = sa.Column(sa.Integer, default=_seq_len, nullable=False)
    seq = sa.Column(sa.Text, nullable=True)

    # methods:


class SeqAnno(Base):
    __tablename__ = "seq_anno"
    __table_args__ = (
        sa.Index(
            "seq_anno_ac_unique_in_origin", "origin_id", "ac", unique=True),
    )

    # columns:
    seq_anno_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    seq_id = sa.Column(sa.Text, sa.ForeignKey("seq.seq_id", onupdate="CASCADE", ondelete="CASCADE"), index=True)
    origin_id = sa.Column(
        sa.Integer, sa.ForeignKey("origin.origin_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    ac = sa.Column(sa.Text, index=True, nullable=False)
    descr = sa.Column(sa.Text)
    added = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.now())

    # relationships:
    origin = sao.relationship("Origin", backref="aliases")
    seq = sao.relationship("Seq", backref="aliases")


class Gene(Base):
    __tablename__ = "gene"

    # columns:
    hgnc = sa.Column(sa.Text, primary_key=True)
    maploc = sa.Column(sa.Text)
    descr = sa.Column(sa.Text)
    summary = sa.Column(sa.Text)
    aliases = sa.Column(sa.Text)
    added = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.now())

    # methods:


class Transcript(Base):
    """class representing unique transcripts, as defined by unique
    accessions (only).

    """
    __tablename__ = "transcript"
    __table_args__ = (
        sa.CheckConstraint(
            "cds_start_i <= cds_end_i", "cds_start_i_must_be_le_cds_end_i"),
    )

    # columns:
    ac = sa.Column(sa.Text, primary_key=True)
    origin_id = sa.Column(
        sa.Integer, sa.ForeignKey("origin.origin_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    hgnc = sa.Column(sa.Text)  # , sa.ForeignKey("gene.hgnc"))
    cds_start_i = sa.Column(sa.Integer) #, nullable=False)
    cds_end_i = sa.Column(sa.Integer) #, nullable=False)
    cds_md5 = sa.Column(sa.Text, index=True)
    added = sa.Column(
        sa.DateTime, default=datetime.datetime.now(), nullable=False)

    # relationships:
    origin = sao.relationship("Origin", backref="transcripts")


class ExonSet(Base):
    __tablename__ = "exon_set"
    __table_args__ = (
        # TODO: Drop ExonSet unique constraint to support degenerate mappings
        sa.UniqueConstraint("tx_ac", "alt_ac", "alt_aln_method",
                            name="<transcript,reference,method> must be unique"),
    )

    # columns:
    exon_set_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    tx_ac = sa.Column(sa.Text, sa.ForeignKey("transcript.ac", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    # TODO: alt_ac should be seq_id -- a reference to a sequence hash
    alt_ac = sa.Column(sa.Text, nullable=False)
    alt_strand = sa.Column(sa.SmallInteger, nullable=False)
    alt_aln_method = sa.Column(sa.Text, nullable=False)
    added = sa.Column(
        sa.DateTime, default=datetime.datetime.now(), nullable=False)

    # relationships:
    transcript = sao.relationship("Transcript", backref="exon_sets")

    # methods
    def exons_se_i(self, transcript_order=False):
        """return exon [start_i,end_i) pairs in reference sequence order, or transcript order if requested"""
        rev = transcript_order and self.alt_strand == -1
        return [(e.start_i, e.end_i) for e in sorted(self.exons, key=lambda e: e.start_i, reverse=rev)]

    def exons_as_str(self, transcript_order=False):
        """return exon [start_i,end_i) pairs in reference sequence order, or transcript order if requested"""
        rev = transcript_order and self.alt_strand == -1
        return ";".join("{e.start_i},{e.end_i}".format(e=e)
                        for e in sorted(self.exons, key=lambda e: e.start_i, reverse=rev))


class Exon(Base):
    __tablename__ = "exon"
    __table_args__ = (
        sa.CheckConstraint("start_i < end_i", "exon_start_i_must_be_lt_end_i"),
        sa.UniqueConstraint(
            "exon_set_id", "start_i", name="start_i_must_be_unique_in_exon_set"),
        sa.UniqueConstraint(
            "exon_set_id", "end_i", name="end_i_must_be_unique_in_exon_set"),
    )

    def __unicode___(self):
        return "[{self.start_i},{self.end_i})".format(self=self)

    # columns:
    exon_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    exon_set_id = sa.Column(
        sa.Integer, sa.ForeignKey("exon_set.exon_set_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    start_i = sa.Column(sa.Integer, nullable=False)
    end_i = sa.Column(sa.Integer, nullable=False)
    ord = sa.Column(sa.Integer, nullable=False)
    name = sa.Column(sa.Text)

    # relationships:
    exon_set = sao.relationship("ExonSet", backref="exons")


class ExonAln(Base):
    __tablename__ = "exon_aln"
    __table_args__ = (
    )

    # columns:
    exon_aln_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    tx_exon_id = sa.Column(
        sa.Integer, sa.ForeignKey("exon.exon_id", onupdate="CASCADE", ondelete="CASCADE"), index=True, nullable=False)
    alt_exon_id = sa.Column(
        sa.Integer, sa.ForeignKey("exon.exon_id", onupdate="CASCADE", ondelete="CASCADE"), index=True, nullable=False)
    cigar = sa.Column(sa.Text, nullable=False)
    added = sa.Column(
        sa.DateTime, default=datetime.datetime.now(), nullable=False)
    tx_aseq = sa.Column(sa.Text, nullable=True)
    alt_aseq = sa.Column(sa.Text, nullable=True)

    # relationships:
    tx_exon = sao.relationship(
        "Exon", backref="tx_aln", foreign_keys=[tx_exon_id])
    alt_exon = sao.relationship(
        "Exon", backref="alt_aln", foreign_keys=[alt_exon_id])

    # methods:


class AssociatedAccessions(Base):
    __tablename__ = "associated_accessions"
    __table_args__ = (
        sa.Index("unique_pair_in_origin", "origin", "tx_ac", "pro_ac", unique=True),
        sa.Index("associated_accessions_pro_ac", "pro_ac"),
        sa.Index("associated_accessions_tx_ac", "tx_ac"),
        {"comment": "transcript-protein accession pairs associated in source databases"},
    )

    # columns:
    associated_accession_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    tx_ac = sa.Column(sa.Text, nullable=False)
    pro_ac = sa.Column(sa.Text, nullable=False)
    origin = sa.Column(sa.Text, nullable=False)
    added = sa.Column(
        postgresql.TIMESTAMP(timezone=True),
        server_default=sqlalchemy.sql.functions.now(),
        nullable=False,
    )


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
