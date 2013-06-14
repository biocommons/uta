"""Schema for Universal Transcript Archive
"""

import datetime, hashlib

import sqlalchemy as sa
import sqlalchemy.orm as sao
import sqlalchemy.ext.declarative as saed

#schema_version = '0'
#schema_name = 'uta'+schema_version
schema_qual = ''

Base = saed.declarative_base()


def seq_hash(context):
    if 'seq' in context.current_parameters:
        return hashlib.md5(context.current_parameters['seq']).hexdigest()
    return None


class Meta(Base):
    __tablename__ = 'meta'
    #__table_args__ = {'schema' : schema_name}
    key = sa.Column(sa.String, primary_key=True, nullable=False, index=True)
    value = sa.Column(sa.String, nullable=False)


class Exon(Base):
    __tablename__ = 'exon'
    #__table_args__ = {'schema' : schema_name}
    exon_id = sa.Column(sa.Integer, sa.Sequence('exon_id_seq'), primary_key=True, index=True)
    transcript_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'transcript.transcript_id'), nullable=False)
    start_i = sa.Column(sa.Integer, nullable=False)
    end_i = sa.Column(sa.Integer, nullable=False)
    name = sa.Column(sa.String)
    seq = sa.Column(sa.String)
    transcript = sao.relationship('Transcript', backref='transcript', uselist=False)

class ExonAlignment(Base):
    __tablename__ = 'exon_alignment'
    __table_args__ = (
        #sa.CheckConstraint('exon_id1 < exon_id2'),
        #{'schema' : schema_name}
        )
    exon_alignment_id = sa.Column(sa.Integer, sa.Sequence('exon_alignment_id_seq'), primary_key=True, index=True)
    added = sa.Column(sa.DateTime, default=datetime.datetime.now(), nullable=False)
    r_exon_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'exon.exon_id'), nullable=False)
    q_exon_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'exon.exon_id'), nullable=False)
    cigar = sa.Column(sa.String, nullable=False)
    alignment = sa.Column(sa.String, nullable=True)
    url = sa.Column(sa.String, nullable=True)
    r_exon = sao.relationship('Exon', backref='r_alignments', foreign_keys=[r_exon_id])
    q_exon = sao.relationship('Exon', backref='q_alignments', foreign_keys=[q_exon_id])

class Gene(Base):
    __tablename__ = 'gene'
    __table_args__ = (
        sa.CheckConstraint('strand = -1 or strand = 1', 'strand_is_plus_or_minus_1'),
        #{'schema' : schema_name}
        )
    gene_id = sa.Column(sa.Integer, sa.Sequence('gene_id_seq'), primary_key=True, index=True)
    added = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.now() )
    gene = sa.Column(sa.String, index=True, unique=True, nullable=False)
    maploc = sa.Column(sa.String)
    strand = sa.Column(sa.SMALLINT)
    descr = sa.Column(sa.String)
    summary = sa.Column(sa.String)
    def __repr__(self):
        return '{self.__class__.__name__}<gene={self.gene}; descr={self.descr}>'.format(
            self=self,len=len(self.seq))


class NSeq(Base):
    __tablename__ = 'nseq'
    #__table_args__ = {'schema' : schema_name}
    nseq_id = sa.Column(sa.Integer, sa.Sequence('nseq_id_seq'), primary_key=True, index=True)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'origin.origin_id'), nullable=False)
    ac = sa.Column(sa.String, nullable=False)
    added = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.now() )
    md5 = sa.Column(sa.String, nullable=True, default=seq_hash, onupdate=seq_hash)
    seq = sa.Column(sa.String, nullable=True)
    origin = sao.relationship("Origin", backref="nseqs")
    def __repr__(self):
        return '{self.__class__.__name__}<ac={self.ac}; seq({len})={self.seq}>'.format(
            self=self,len=len(self.seq))

class Origin(Base):
    __tablename__ = 'origin'
    #__table_args__ = {'schema' : schema_name}
    origin_id = sa.Column(sa.Integer, sa.Sequence('origin_id_seq'), primary_key=True, index=True)
    name = sa.Column(sa.String, nullable=False)
    added = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.now() )
    url = sa.Column(sa.String, nullable=True)
    url_fmt = sa.Column(sa.String, nullable=True)
    def __repr__(self):
        return '{self.__class__.__name__}<name={self.name}; url={self.url}>'.format(
            self=self,len=len(self.seq))

class OriginTranscriptAlias(Base):
    __tablename__ = 'origin_transcript_alias'
    #__table_args__ = {'schema' : schema_name}
    origin_transcript_alias_id = sa.Column(sa.Integer, sa.Sequence('origin_transcript_alias_id_seq'), primary_key=True, index=True)
    transcript_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'transcript.transcript_id'), nullable=False, index=True)
    origin_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'origin.origin_id'), nullable=False, index=True)
    added = sa.Column(sa.DateTime, default=datetime.datetime.now(), nullable=False)
    alias = sa.Column(sa.String, index=True)
    transcript = sao.relationship('Transcript', backref='transcript_origins')
    origin = sao.relationship('Origin', backref='origin_transcripts')
    def __repr__(self):
        return '{self.__class__.__name__}<origin={self.origin.name}; transcript alias={self.alias}>'.format(
            self=self,len=len(self.seq))


class Transcript(Base):
    __tablename__ = 'transcript'
    __table_args__ = (
        sa.CheckConstraint('strand = -1 or strand = 1', 'strand_is_plus_or_minus_1'),
        #{'schema' : schema_name}
        )
    transcript_id = sa.Column(sa.Integer, sa.Sequence('transcript_id_seq'), primary_key=True, index=True)
    nseq_id = sa.Column(sa.Integer, sa.ForeignKey(schema_qual+'nseq.nseq_id'), nullable=False)
    added = sa.Column(sa.DateTime, default=datetime.datetime.now(), nullable=False)
    strand = sa.Column(sa.SMALLINT, nullable=False)
    cds_start_i = sa.Column(sa.Integer, nullable=False)
    cds_end_i = sa.Column(sa.Integer, nullable=False)
    nseq = sao.relationship('NSeq', backref='nseq', uselist=False)
    def __repr__(self):
        return '{self.__class__.__name__}<aliases={self.aliases}; descr={self.descr}>'.format(
            self=self,len=len(self.seq))




if __name__ == '__main__':
    import uta.sa_models as usam # for copy-pase convenience with other code
    import sqlalchemy.orm as so

    engine = sa.create_engine('sqlite:///:memory:')
    
    Session = so.sessionmaker(bind=engine)
    session = Session()
    
    usam.Base.metadata.create_all(engine) 
    session.commit()

    o = usam.Origin(name='Test')
    session.add(o)

    n = usam.NSeq(ac='NM_01234.5',seq='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    n.origin = o
    session.add(n)

    t = usam.Transcript(strand=1,cds_start_i=5,cds_end_i=10)
    t.nseq = n
    session.add(t)

    ota = usam.OriginTranscriptAlias(alias='NM_01234.5')
    ota.origin = o
    ota.transcript = t
    session.add(ota)

    session.commit()
