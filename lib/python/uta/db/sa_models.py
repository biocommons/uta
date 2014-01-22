"""Schema for Universal Transcript Archive

NOTE: This code and schema are NOT currently in use.  This was exploratory work.  It is incomplete and untested.
It requires schema support (i.e., sqlite won't work)
"""

import datetime, hashlib

import sqlalchemy as sa
import sqlalchemy.orm as sao
import sqlalchemy.ext.declarative as saed


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
    def __str__(self):
        return unicode(self).encode('utf-8')

class Meta(Base,UTABase):
    __tablename__ = 'meta'
    __table_args__ = (
        {'schema' : schema_name},
        )
    key = sa.Column(sa.String, primary_key = True, nullable = False, index = True)
    value = sa.Column(sa.String, nullable = False)


class Origin(Base,UTABase):
    __tablename__ = 'origin'
    __table_args__ = (
        {'schema' : schema_name},
        )

    # columns:
    origin_id = sa.Column(sa.Integer, sa.Sequence('origin_id_seq'), primary_key = True, index = True)
    name = sa.Column(sa.String, nullable = False, unique = True)
    updated = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now(), onupdate = datetime.datetime.now() )
    url = sa.Column(sa.String, nullable = True)
    url_ac_fmt = sa.Column(sa.String, nullable = True)

    # methods:
    def __unicode__(self):
        return '{self.__class__.__name__}<name={self.name}; updated={self.updated}; url={self.url}>'.format(
            self = self)


class DNASeq(Base,UTABase):
    __tablename__ = 'dnaseq'
    __table_args__ = (
        {'schema' : schema_name},
        )

    def _seq_hash(context):
        seq = context.current_parameters['seq']
        return None if seq is None else hashlib.md5(seq).hexdigest()

    # columns:
    dnaseq_id = sa.Column(sa.Integer, sa.Sequence('dnaseq_id_seq'), primary_key = True, index = True)
    md5 = sa.Column(sa.String, nullable=True, unique=True, default=_seq_hash)
    seq = sa.Column(sa.String, nullable = True)

    # methods:
    def __unicode__(self):
        return '{self.__class__.__name__}<ac={self.ac}; seq({len})={self.seq}>'.format(
            self = self,len = len(self.seq) if self.seq else '?')


class DNASeqOriginAlias(Base,UTABase):
    __tablename__ = 'dnaseq_origin_alias'
    __table_args__ = (
        sa.Index('dnaseqoriginalias_ac_unique_in_origin', 'origin_id', 'alias', unique = True),
        {'schema' : schema_name},
        )

    # columns:
    dnaseq_origin_alias_id = sa.Column(sa.Integer, sa.Sequence('dnaseq_origin_alias_seq'), primary_key = True, index = True)
    dnaseq_id = sa.Column(sa.Integer, sa.ForeignKey('dnaseq.dnaseq_id'))
    origin_id = sa.Column(sa.Integer, sa.ForeignKey('origin.origin_id'), nullable = False)
    alias = sa.Column(sa.Text, index = True)
    added = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now() )

    # relationships:
    origin = sao.relationship('Origin', backref = 'aliases')
    dnaseq = sao.relationship('DNASeq', backref = 'aliases')


class Gene(Base,UTABase):
    __tablename__ = 'gene'
    __table_args__ = (
        {'schema' : schema_name},
        )

    # columns:
    gene_id = sa.Column(sa.Integer, sa.Sequence('gene_seq'), primary_key = True, index = True)
    hgnc = sa.Column(sa.String, index = True, unique = True, nullable = False)
    maploc = sa.Column(sa.String)
    descr = sa.Column(sa.String)
    summary = sa.Column(sa.String)
    aliases = sa.Column(sa.Text)
    added = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now() )

    # methods:
    def __unicode__(self):
        return '{self.__class__.__name__}<gene={self.name}; maploc={self.maploc}; descr={self.descr}>'.format(
            self = self)


class Transcript(Base,UTABase):
    __tablename__ = 'transcript'
    __table_args__ = (
        sa.CheckConstraint('cds_start_i <= cds_end_i', 'cds_start_i_must_be_le_cds_end_i'),
        sa.Index('transcript_ac_unique_in_origin', 'origin_id', 'ac', unique = True),
        {'schema' : schema_name},
        )

    # columns:
    transcript_id = sa.Column(sa.Integer, sa.Sequence('transcript_id_seq'), primary_key = True, index = True)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey('origin.origin_id'), nullable = False)
    ac = sa.Column(sa.String, nullable = False)
    gene_id = sa.Column(sa.Integer, sa.ForeignKey('gene.gene_id'))
    dnaseq_id = sa.Column(sa.Integer, sa.ForeignKey('dnaseq.dnaseq_id'))
    strand = sa.Column(sa.SmallInteger, nullable = False)
    cds_start_i = sa.Column(sa.Integer, nullable = False)
    cds_end_i = sa.Column(sa.Integer, nullable = False)
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)

    # relationships:
    origin = sao.relationship('Origin', backref = 'transcripts')
    gene = sao.relationship('Gene', backref = 'transcripts')
    dnaseq = sao.relationship('DNASeq')

    # methods:
    def __unicode__(self):
        return '{self.__class__.__name__}<origin={self.origin.name},ac={self.ac},gene={self.gene.name}>'.format(
            self = self)


class ExonSet(Base,UTABase):
    __tablename__ = 'exon_set'
    __table_args__ = (
        sa.UniqueConstraint('transcript_id','ref_dnaseq_id',name='transcript_on_ref_dnaseq_must_be_unique'),
        {'schema' : schema_name},
        )
    
    # columns:
    exon_set_id = sa.Column(sa.Integer, sa.Sequence('exon_set_id_seq'), primary_key = True, index = True)
    transcript_id = sa.Column(sa.Integer, sa.ForeignKey('transcript.transcript_id'), nullable = False)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey('origin.origin_id'), nullable = False)
    ref_dnaseq_id = sa.Column(sa.Integer, sa.ForeignKey('dnaseq.dnaseq_id'), nullable = False)
    ref_strand = sa.Column(sa.SmallInteger, nullable = False)
    method = sa.Column(sa.Text, nullable = False)
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)
    
    # relationships:
    transcript = sao.relationship('Transcript', backref = 'exon_sets')
    target_dnaseq = sao.relationship('DNASeq', backref = 'exon_sets')
    origin = sao.relationship('Origin', backref = 'exon_sets')

    # properties:
    # def tx_md5 = 
    # def cds_md5 = 
    # def exon_start_i(self):
    # def exon_end_i(self):
    @property
    def is_primary(self):
        return self.ref_dnaseq_id == self.transcript.dnaseq_id

    # methods:
    def __unicode__(self):
        return '{self.__class__.__name__}<origin={self.origin.name},transcript={self.transcript.ac},ref={self.ref_dnaseq.ac},primary={self.is_primary},exons={nexons}>'.format(
            self = self, nexons = len(self.exons))


class Exon(Base,UTABase):
    __tablename__ = 'exon'
    __table_args__ = (
        sa.CheckConstraint('start_i < end_i', 'exon_start_i_must_be_lt_end_i'),
        sa.UniqueConstraint('exon_set_id','start_i',name='start_i_must_be_unique_in_exon_set'),
        sa.UniqueConstraint('exon_set_id','end_i',name='end_i_must_be_unique_in_exon_set'),
        {'schema' : schema_name},
        )

    # columns:
    exon_id = sa.Column(sa.Integer, sa.Sequence('exon_id_seq'), primary_key = True, index = True)
    exon_set_id = sa.Column(sa.Integer, sa.ForeignKey('exon_set.exon_set_id'), nullable = False)
    start_i = sa.Column(sa.Integer, nullable = False)
    end_i = sa.Column(sa.Integer, nullable = False)
    name = sa.Column(sa.String)

    # relationships:
    exon_set = sao.relationship('ExonSet', backref = 'exons')

    # properties:
    # def seq():

    # methods:
    def __unicode__(self):
        return '{self.__class__.__name__}<{self.exon_set.transcript.ac},{self.name},@{self.exon_set.ref_dnaseq.ac}:[{self.start_i}:{self.end_i}]>'.format(
            self = self)


class ExonAlignment(Base,UTABase):
    __tablename__ = 'exon_alignment'
    __table_args__ = (
        {'schema' : schema_name},
        )

    # columns:
    exon_alignment_id = sa.Column(sa.Integer, sa.Sequence('exon_alignment_id_seq'), primary_key = True, index = True)
    tx_exon_id = sa.Column(sa.Integer, sa.ForeignKey('exon.exon_id'), nullable = False)
    ref_exon_id = sa.Column(sa.Integer, sa.ForeignKey('exon.exon_id'), nullable = False)
    cigar = sa.Column(sa.String, nullable = False)
    url = sa.Column(sa.String, nullable = True)
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)

    # relationships:
    tx_exon = sao.relationship('Exon', backref = 'tx_alignment', foreign_keys = [tx_exon_id])
    ref_exon = sao.relationship('Exon', backref = 'ref_alignment', foreign_keys = [ref_exon_id])

    # methods:
    def __unicode__(self):
        return '{self.__class__.__name__}<{self.tx_exon} ~ {self.ref_exon}>'.format(self = self)



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
