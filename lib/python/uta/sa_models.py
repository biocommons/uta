"""Schema for Universal Transcript Archive
"""

# TODO: review for table uniqueness criteria
# TODO: __str__ for all
# TODO: FK backrefs
# TODO: " -> '

import datetime, hashlib

import sqlalchemy as sa
import sqlalchemy.orm as sao
import sqlalchemy.ext.declarative as saed

schema_version = '0'
#schema_name = 'uta'+schema_version
schema_qual = ''

Base = saed.declarative_base()


class Meta(Base):
    __tablename__ = 'meta'
    #__table_args__ = {'schema' : schema_name}
    key = sa.Column(sa.String, primary_key = True, nullable = False, index = True)
    value = sa.Column(sa.String, nullable = False)


class Origin(Base):
    __tablename__ = 'origin'
    #__table_args__ = {'schema' : schema_name}

    # columns:
    origin_id = sa.Column(sa.Integer, sa.Sequence('origin_id_seq'), primary_key = True, index = True)
    name = sa.Column(sa.String, nullable = False)
    added = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now() )
    updated = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now(), onupdate = datetime.datetime.now() )
    url = sa.Column(sa.String, nullable = True)
    url_ac_fmt = sa.Column(sa.String, nullable = True)

    # methods:
    def __str__(self):
        return '{self.__class__.__name__}<name={self.name}; updated={self.updated}; url={self.url}>'.format(
            self = self)


class Gene(Base):
    __tablename__ = 'gene'
    __table_args__ = (
        sa.CheckConstraint('strand = -1 or strand = 1', 'strand_is_plus_or_minus_1'),
        #{'schema' : schema_name}
        )

    # columns:
    gene_id = sa.Column(sa.Integer, sa.Sequence('gene_id_seq'), primary_key = True, index = True)
    origin_id = sa.Column(sa.Integer, sa.Sequence('origin_id_seq'), index = True)
    name = sa.Column(sa.String, index = True, unique = True, nullable = False)
    maploc = sa.Column(sa.String)
    strand = sa.Column(sa.SMALLINT)
    added = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now() )
    descr = sa.Column(sa.String)
    summary = sa.Column(sa.String)

    # properties:
    @property
    def strand_pm(self):
        return '' if self.strand is None else '-' if self.strand == -1 else '+'

    # methods:
    def __str__(self):
        return '{self.__class__.__name__}<gene={self.name}; maploc={self.strand_pm}{self.maploc}; descr={self.descr}>'.format(
            self = self)


class NSeq(Base):
    def _seq_hash(context):
        seq = context.current_parameters['seq']
        if seq is not None:
            return hashlib.md5(seq).hexdigest() 
        return None 

    __tablename__ = 'nseq'
    #__table_args__ = {'schema' : schema_name}

    # columns:
    nseq_id = sa.Column(sa.Integer, sa.Sequence('nseq_id_seq'), primary_key = True, index = True)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'origin.origin_id'), nullable = False)
    ac = sa.Column(sa.String, nullable = False)
    added = sa.Column(sa.DateTime, nullable = False, default = datetime.datetime.now() )
    md5 = sa.Column(sa.String, nullable = True, default =_seq_hash)
    seq = sa.Column(sa.String, nullable = True)

    # relationships:
    origin = sao.relationship('Origin', backref = 'nseqs')

    # methods:
    def __str__(self):
        return '{self.__class__.__name__}<ac={self.ac}; seq({len})={self.seq}>'.format(
            self = self,len = len(self.seq) if self.seq else '?')
    

class Transcript(Base):
    __tablename__ = 'transcript'
    __table_args__ = (
        sa.Index('ac_unique_in_origin', 'origin_id', 'ac', unique = True),
        #{'schema' : schema_name}
        )

    # columns:
    transcript_id = sa.Column(sa.Integer, sa.Sequence('transcript_id_seq'), primary_key = True, index = True)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'origin.origin_id'), nullable = False)
    ac = sa.Column(sa.String, nullable = False)
    nseq_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'nseq.nseq_id'), nullable = False)
    gene_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'gene.gene_id'))
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)

    # relationships:
    origin = sao.relationship('Origin', backref = 'transcripts')
    nseq = sao.relationship('NSeq')
    gene = sao.relationship('Gene', backref = 'transcripts')

    # methods:
    def __str__(self):
        return '{self.__class__.__name__}<origin={self.origin.name},ac={self.ac},gene={self.gene.name}>'.format(
            self = self)


class ExonSet(Base):
    __tablename__ = 'exon_set'
    __table_args__ = (
        sa.CheckConstraint('cds_start_i < cds_end_i', 'cds_start_i_must_be_lt_cds_end_i'),
        )
    
    # columns:
    exon_set_id = sa.Column(sa.Integer, sa.Sequence('exon_set_id_seq'), primary_key = True, index = True)
    transcript_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'transcript.transcript_id'), nullable = False)
    ref_nseq_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'nseq.nseq_id'), nullable = False)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'origin.origin_id'), nullable = False)
    strand = sa.Column(sa.SMALLINT, nullable = False)
    cds_start_i = sa.Column(sa.Integer, nullable = False)
    cds_end_i = sa.Column(sa.Integer, nullable = False)
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)
    
    # relationships:
    transcript = sao.relationship('Transcript', backref = 'exon_sets')
    ref_nseq = sao.relationship('NSeq', backref = 'exon_sets')
    origin = sao.relationship('Origin', backref = 'exon_sets')

    # properties:
    # def tx_md5 = 
    # def cds_md5 = 
    # def exon_start_i(self):
    # def exon_end_i(self):
    @property
    def is_primary(self):
        return self.ref_nseq_id == self.transcript.nseq_id

    # methods:
    def __str__(self):
        return '{self.__class__.__name__}<origin={self.origin.name},transcript={self.transcript.ac},ref={self.ref_nseq.ac},primary={self.is_primary},exons={nexons}>'.format(
            self = self, nexons = len(self.exons))


class Exon(Base):
    __tablename__ = 'exon'
    __table_args__ = (
        sa.CheckConstraint('start_i < end_i', 'exon_start_i_must_be_lt_end_i'),
        # {'schema' : schema_name}
        )

    # columns:
    exon_id = sa.Column(sa.Integer, sa.Sequence('exon_id_seq'), primary_key = True, index = True)
    exon_set_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'exon_set.exon_set_id'), nullable = False)
    start_i = sa.Column(sa.Integer, nullable = False)
    end_i = sa.Column(sa.Integer, nullable = False)
    name = sa.Column(sa.String)
    seq = sa.Column(sa.String)

    # relationships:
    exon_set = sao.relationship('ExonSet', backref = 'exons')

    # methods:
    def __str__(self):
        return '{self.__class__.__name__}<{self.exon_set.transcript.ac},{self.name},@{self.exon_set.ref_nseq.ac}:[{self.start_i}:{self.end_i}]>'.format(
            self = self)


class ExonAlignment(Base):
    __tablename__ = 'exon_alignment'
    __table_args__ = (
        #sa.CheckConstraint('exon_id1 < exon_id2'),
        #{'schema' : schema_name}
        )

    # columns:
    exon_alignment_id = sa.Column(sa.Integer, sa.Sequence('exon_alignment_id_seq'), primary_key = True, index = True)
    tx_exon_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'exon.exon_id'), nullable = False)
    ref_exon_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'exon.exon_id'), nullable = False)
    cigar = sa.Column(sa.String, nullable = False)
    alignment = sa.Column(sa.String, nullable = True)
    url = sa.Column(sa.String, nullable = True)
    added = sa.Column(sa.DateTime, default = datetime.datetime.now(), nullable = False)

    # relationships:
    tx_exon = sao.relationship('Exon', backref = 'r_alignments', foreign_keys =[tx_exon_id])
    ref_exon = sao.relationship('Exon', backref = 'q_alignments', foreign_keys =[ref_exon_id])

    # methods:
    def __str__(self):
        return '{self.__class__.__name__}<{self.tx_exon} ~ {self.ref_exon}>'.format(self = self)

