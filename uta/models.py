"""Schema for Universal Transcript Archive
"""

import datetime, hashlib

import sqlalchemy as sa
import sqlalchemy.orm as sao
import sqlalchemy.ext.declarative as saed

import uta.utils


############################################################################
## Implmentation notes
# * PK-FK object relationships are declared exclusively on the dependent
# object, that is, the FK side. (SQLAlchemy permits either, but mixing
# styles screws with my head too much.


############################################################################
## schema name support
# also see etc/uta.conf

schema_version = '1'
use_schema = True
if use_schema:
    schema_name = 'uta'+schema_version
    schema_name_dot = schema_name + '.'
else:
    schema_name = None
    schema_name_dot = ''


############################################################################

Base = saed.declarative_base(
    metadata=sa.MetaData(schema=schema_name)
    )


class UTABase(object):
    pass
    #def __str__(self):
    #    return unicode(self).encode('utf-8')


class Meta(Base,UTABase):
    __tablename__ = 'meta'
    __table_args__ = (
        {'schema' : schema_name},
        )
    key = sa.Column(sa.Text, primary_key = True, nullable = False)
    value = sa.Column(sa.Text, nullable = False)


class Origin(Base,UTABase):
    __tablename__ = 'origin'
    __table_args__ = (
        {'schema' : schema_name},
        )

    # columns:
    origin_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.Text, nullable=False, unique=True)
    descr = sa.Column(sa.Text)
    updated = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.now(), onupdate=datetime.datetime.now() )
    url = sa.Column(sa.Text, nullable=True)
    url_ac_fmt = sa.Column(sa.Text, nullable=True)

    # methods:
    def tickle_update(self):
        self.updated = datetime.datetime.now()


class AlnMethod(Base,UTABase):
    __tablename__ = 'aln_method'
    __table_args__ = (
        {'schema' : schema_name},
        )

    aln_method_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.Text, unique=True)
    descr = sa.Column(sa.Text)


class Gene(Base,UTABase):
    __tablename__ = 'gene'
    __table_args__ = (
        {'schema' : schema_name},
        )

    # columns:
    hgnc = sa.Column(sa.Text, primary_key=True)
    maploc = sa.Column(sa.Text)
    descr = sa.Column(sa.Text)
    summary = sa.Column(sa.Text)
    aliases = sa.Column(sa.Text)
    added = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.now() )

    # methods:


class Transcript(Base,UTABase):
    """class representing unique transcripts, as defined by unique <seq_id,cds_se,exons_se_i>
    """
    __tablename__ = 'transcript'
    __table_args__ = (
        sa.CheckConstraint('cds_start_i <= cds_end_i', 'cds_start_i_must_be_le_cds_end_i'),
        {'schema' : schema_name},
        )

    # columns:
    ac = sa.Column(sa.Text, primary_key=True)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey('origin.origin_id'), nullable=False)
    hgnc = sa.Column(sa.Text, sa.ForeignKey('gene.hgnc'))
    cds_start_i = sa.Column(sa.Integer, nullable=False)
    cds_end_i = sa.Column(sa.Integer, nullable=False)
    added = sa.Column(sa.DateTime, default=datetime.datetime.now(), nullable=False)

    # relationships:
    origin = sao.relationship('Origin', backref='transcripts')
    gene = sao.relationship('Gene', backref='transcripts')


class ExonSet(Base,UTABase):
    __tablename__ = 'exon_set'
    __table_args__ = (
        sa.UniqueConstraint('tx_ac','alt_ac','alt_aln_method_id',
                            name='<transcript,reference,method> must be unique'),
        {'schema' : schema_name},
        )

    # columns:
    exon_set_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    tx_ac = sa.Column(sa.Text, sa.ForeignKey('transcript.ac'), nullable=False)
    alt_ac = sa.Column(sa.Text, nullable=False)
    alt_strand = sa.Column(sa.SmallInteger, nullable=False)
    alt_aln_method_id = sa.Column(sa.Integer, sa.ForeignKey('aln_method.aln_method_id'), nullable=False)
    added = sa.Column(sa.DateTime, default=datetime.datetime.now(), nullable=False)
    
    # relationships:
    transcript = sao.relationship('Transcript', backref='exon_sets')
    
    def exons_se(self,transcript_order=False):
        """return exon [start_i,end_i) pairs in reference sequence order, or transcript order if requested"""
        rev = transcript_order and self.ref_strand == -1
        return sorted([(e.start_i,e.end_i) for e in self.exons], reverse=rev)

    # methods:


class Exon(Base,UTABase):
    __tablename__ = 'exon'
    __table_args__ = (
        sa.CheckConstraint('start_i < end_i', 'exon_start_i_must_be_lt_end_i'),
        sa.UniqueConstraint('exon_set_id','start_i',name='start_i_must_be_unique_in_exon_set'),
        sa.UniqueConstraint('exon_set_id','end_i',name='end_i_must_be_unique_in_exon_set'),
        {'schema' : schema_name},
        )

    def __unicode___(self):
        return "[{self.start_i},{self.end_i})".format(self=self)

    # columns:
    exon_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    exon_set_id = sa.Column(sa.Integer, sa.ForeignKey('exon_set.exon_set_id'), nullable=False)
    start_i = sa.Column(sa.Integer, nullable=False)
    end_i = sa.Column(sa.Integer, nullable=False)
    ord = sa.Column(sa.Integer, nullable=False)
    name = sa.Column(sa.Text)

    # relationships:
    exon_set = sao.relationship('ExonSet', backref='exons')


class ExonAln(Base,UTABase):
    __tablename__ = 'exon_aln'
    __table_args__ = (
        {'schema' : schema_name},
        )

    # columns:
    exon_aln_id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    tx_exon_id = sa.Column(sa.Integer, sa.ForeignKey('exon.exon_id'), nullable=False)
    alt_exon_id = sa.Column(sa.Integer, sa.ForeignKey('exon.exon_id'), nullable=False)
    cigar = sa.Column(sa.Text, nullable=False)
    added = sa.Column(sa.DateTime, default=datetime.datetime.now(), nullable=False)
    tx_seq = sa.Column(sa.Text, nullable=False)
    alt_seq = sa.Column(sa.Text, nullable=False)

    # relationships:
    tx_exon = sao.relationship('Exon', backref='tx_aln', foreign_keys=[tx_exon_id])
    alt_exon = sao.relationship('Exon', backref='alt_aln', foreign_keys=[alt_exon_id])

    # methods:



## <LICENSE>
## Copyright 2014 UTA Contributors (https://bitbucket.org/invitae/uta)
## 
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
## 
##     http://www.apache.org/licenses/LICENSE-2.0
## 
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## </LICENSE>
