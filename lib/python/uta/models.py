import datetime

from sqlalchemy import Column, Integer, String, Sequence, DateTime, text
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

schema_version = 1

Base = declarative_base()

class Origin(Base):
    __tablename__ = 'origin'
    origin_id = Column(Integer, Sequence('origin_id_seq'), primary_key=True, index=True)
    added = Column(DateTime, nullable=False, default=datetime.datetime.now() )
    name = Column(String, nullable=False)
    url = Column(String, nullable=True)
    url_fmt = Column(String, nullable=True)

class NASeq(Base):
    __tablename__ = 'na_seq'
    naseq_id = Column(Integer, Sequence('na_seq_id_seq'), primary_key=True, index=True)
    origin_id = Column(Integer, ForeignKey('origin.origin_id'), nullable=False)
    added = Column(DateTime, nullable=False, default=datetime.datetime.now() )
    ac = Column(String, nullable=False)
    md5 = Column(String, nullable=True)
    seq = Column(String, nullable=True)

class Transcript(Base):
    __tablename__ = 'transcript'
    transcript_id = Column(Integer, Sequence('transcript_id_seq'), primary_key=True, index=True)
    origin_id = Column(Integer, ForeignKey('origin.origin_id'), nullable=False)
    added = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    cds_start_i = Column(Integer, nullable=False)
    cds_end_i = Column(Integer, nullable=False)

class Exon(Base):
    __tablename__ = 'exon'
    exon_id = Column(Integer, Sequence('exon_id_seq'), primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey('transcript.transcript_id'), nullable=False)
    start_i = Column(Integer, nullable=False)
    end_i = Column(Integer, nullable=False)
    name = Column(String)
    
class ExonAlignment(Base):
    __tablename__ = 'exon_alignment'
    __table_args__ = (
        CheckConstraint('exon_id1 < exon_id2'),
        )
    exon_alignment_id = Column(Integer, Sequence('exon_alignment_id_seq'), primary_key=True, index=True)
    exon_id1 = Column(Integer, ForeignKey('exon.exon_id'), nullable=False)
    exon_id2 = Column(Integer, ForeignKey('exon.exon_id'), nullable=False)
    cigar = Column(String, nullable=False)
    alignment = Column(String, nullable=True)

class Meta(Base):
    __tablename__ = 'meta'
    key = Column(String, primary_key=True, nullable=False, index=True)
    value = Column(String, nullable=False)
