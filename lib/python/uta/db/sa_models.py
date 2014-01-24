"""Schema for Universal Transcript Archive
"""

import datetime, hashlib

import sqlalchemy as sa
import sqlalchemy.orm as sao
import sqlalchemy.ext.declarative as saed


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
    metadata = sa.MetaData(schema=schema_name)
    )


class UTABase(object):
    pass
#    def __str__(self):
#        return unicode(self).encode('utf-8')


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
    origin_id = sa.Column(sa.Integer, autoincrement=True, primary_key = True)
    name = sa.Column(sa.Text, nullable = False, unique = True)
    updated = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now(), onupdate = datetime.datetime.now() )
    url = sa.Column(sa.Text, nullable = True)
    url_ac_fmt = sa.Column(sa.Text, nullable = True)

    # methods:
#    def __unicode__(self):
#        return '{self.__class__.__name__}<name={self.name}; updated={self.updated}; url={self.url}>'.format(
#            self = self)

    def tickle_update(self):
        self.updated = datetime.datetime.now()


class Seq(Base,UTABase):
    __tablename__ = 'seq'
    __table_args__ = (
        {'schema' : schema_name},
        )

    def _seq_hash(context):
        seq = context.current_parameters['seq']
        return None if seq is None else hashlib.md5(seq.upper()).hexdigest()
    def _seq_len(context):
        seq = context.current_parameters['seq']
        return None if seq is None else len(seq)

    # columns:
    seq_id = sa.Column(sa.Text, default=_seq_hash, primary_key = True)
    len = sa.Column(sa.Integer, default=_seq_len, nullable = False)
    seq = sa.Column(sa.Text, nullable = True)

    # methods:
#    def __unicode__(self):
#        return '{self.__class__.__name__}<ac={self.ac}; seq({len})={self.seq}>'.format(
#            self = self,len = len(self.seq) if self.seq else '?')


class SeqOriginAlias(Base,UTABase):
    __tablename__ = 'seq_origin_alias'
    __table_args__ = (
        sa.Index('seqoriginalias_ac_unique_in_origin', 'origin_id', 'alias', unique = True),
        {'schema' : schema_name},
        )

    # columns:
    seq_origin_alias_id = sa.Column(sa.Integer, autoincrement=True, primary_key = True)
    seq_id = sa.Column(sa.Text, sa.ForeignKey('seq.seq_id'))
    origin_id = sa.Column(sa.Integer, sa.ForeignKey('origin.origin_id'), nullable = False)
    alias = sa.Column(sa.Text, index = True)
    descr = sa.Column(sa.Text)
    added = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now() )

    # relationships:
    origin = sao.relationship('Origin', backref = 'aliases')
    seq = sao.relationship('Seq', backref = 'aliases')


class Gene(Base,UTABase):
    __tablename__ = 'gene'
    __table_args__ = (
        {'schema' : schema_name},
        )

    # columns:
    gene_id = sa.Column(sa.Integer, autoincrement=True, primary_key = True)
    hgnc = sa.Column(sa.Text, index = True, unique = True, nullable = False)
    maploc = sa.Column(sa.Text)
    descr = sa.Column(sa.Text)
    summary = sa.Column(sa.Text)
    aliases = sa.Column(sa.Text)
    added = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now() )

    # methods:
#    def __unicode__(self):
#        return '{self.__class__.__name__}<gene={self.name}; maploc={self.maploc}; descr={self.descr}>'.format(
#            self = self)


class Transcript(Base,UTABase):
    __tablename__ = 'transcript'
    __table_args__ = (
        sa.CheckConstraint('cds_start_i <= cds_end_i', 'cds_start_i_must_be_le_cds_end_i'),
        sa.Index('transcript_ac_unique_in_origin', 'origin_id', 'ac', unique = True),
        {'schema' : schema_name},
        )

#    def __unicode__(self):
#        return "Transcript<{tx.transcript_id}; {tx.gene.hgnc}, {tx.seq_id}, [{tx.cds_start_i},{tx.cds_end_i}]>".format(tx=self)

    # columns:
    transcript_id = sa.Column(sa.Integer, autoincrement=True, primary_key = True)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey('origin.origin_id'), nullable = False)
    gene_id = sa.Column(sa.Integer, sa.ForeignKey('gene.gene_id'))
    seq_id = sa.Column(sa.Text, sa.ForeignKey('seq.seq_id'))
    cds_start_i = sa.Column(sa.Integer, nullable = False)
    cds_end_i = sa.Column(sa.Integer, nullable = False)
    ac = sa.Column(sa.Text, nullable = False)
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)

    # relationships:
    origin = sao.relationship('Origin', backref = 'transcripts')
    gene = sao.relationship('Gene', backref = 'transcripts')
    seq = sao.relationship('Seq')

    # methods:
#    def __unicode__(self):
#        return '{self.__class__.__name__}<origin={self.origin.name},ac={self.ac},gene={self.gene.name}>'.format(
#            self = self)


class ExonSet(Base,UTABase):
    __tablename__ = 'exon_set'
    __table_args__ = (
        sa.UniqueConstraint('transcript_id','ref_seq_id','origin_id','method',name='<transcript,reference,origin,method> must be unique'),
        {'schema' : schema_name},
        )

#    def __unicode__(self):
#        return "ExonSet<{es.exon_set_id}; {es.transcript_id},{es.ref_seq_id},{es.origin_id},{es.method}>".format(es=self)

    
    # columns:
    exon_set_id = sa.Column(sa.Integer, autoincrement=True, primary_key = True)
    transcript_id = sa.Column(sa.Integer, sa.ForeignKey('transcript.transcript_id'), nullable = False)
    ref_seq_id = sa.Column(sa.Text, sa.ForeignKey('seq.seq_id'), nullable = False)
    ref_strand = sa.Column(sa.SmallInteger, nullable = False)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey('origin.origin_id'), nullable = False)
    method = sa.Column(sa.Text, nullable = False)
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)
    
    # relationships:
    transcript = sao.relationship('Transcript', backref = 'exon_sets')
    ref_seq = sao.relationship('Seq', backref = 'exon_sets')
    origin = sao.relationship('Origin')

    # properties:
    # def tx_md5 = 
    # def cds_md5 = 
    # def exon_start_i(self):
    # def exon_end_i(self):

    @property
    def is_primary(self):
        return self.ref_seq_id == self.transcript.seq_id

    # methods:
#    def __unicode__(self):
#        return '{self.__class__.__name__}<origin={self.origin.name},transcript={self.transcript.ac},ref={self.ref_seq.ac},primary={self.is_primary},exons={nexons}>'.format(
#            self = self, nexons = len(self.exons))


class Exon(Base,UTABase):
    __tablename__ = 'exon'
    __table_args__ = (
        sa.CheckConstraint('start_i < end_i', 'exon_start_i_must_be_lt_end_i'),
        # TODO: Figure out how to implement no-overlapping constraint
        sa.UniqueConstraint('exon_set_id','start_i',name='start_i_must_be_unique_in_exon_set'),
        sa.UniqueConstraint('exon_set_id','end_i',name='end_i_must_be_unique_in_exon_set'),
        {'schema' : schema_name},
        )

    # columns:
    exon_id = sa.Column(sa.Integer, autoincrement=True, primary_key = True)
    exon_set_id = sa.Column(sa.Integer, sa.ForeignKey('exon_set.exon_set_id'), nullable = False)
    start_i = sa.Column(sa.Integer, nullable = False)
    end_i = sa.Column(sa.Integer, nullable = False)
    name = sa.Column(sa.Text)

    # relationships:
    exon_set = sao.relationship('ExonSet', backref = 'exons')

    @property
    def seq(self):
        seq = self.exon_set.ref_seq.seq
        return None if seq is None else seq[self.start_i:self.end_i]

    # methods:
#    def __unicode__(self):
#        return '{self.__class__.__name__}<{self.exon_set.transcript.ac},{self.name},@{self.exon_set.ref_seq.ac}:[{self.start_i}:{self.end_i}]>'.format(
#            self = self)


class ExonAlignment(Base,UTABase):
    __tablename__ = 'exon_alignment'
    __table_args__ = (
        {'schema' : schema_name},
        )

    # columns:
    exon_alignment_id = sa.Column(sa.Integer, autoincrement=True, primary_key = True)
    tx_exon_id = sa.Column(sa.Integer, sa.ForeignKey('exon.exon_id'), nullable = False)
    ref_exon_id = sa.Column(sa.Integer, sa.ForeignKey('exon.exon_id'), nullable = False)
    cigar = sa.Column(sa.Text, nullable = False)
    url = sa.Column(sa.Text, nullable = True)
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)

    # relationships:
    tx_exon = sao.relationship('Exon', backref = 'tx_alignment', foreign_keys = [tx_exon_id])
    ref_exon = sao.relationship('Exon', backref = 'ref_alignment', foreign_keys = [ref_exon_id])

    # methods:
#    def __unicode__(self):
#        return '{self.__class__.__name__}<{self.tx_exon} ~ {self.ref_exon}>'.format(self = self)



def strand_pm(strand):
    if strand is None: return ''
    elif strand == 1: return '+'
    elif strand == -1: return '-'
    else: return '?'


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
