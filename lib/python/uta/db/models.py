import collections

class Transcript(collections.namedtuple('Transcripts',[
            'ac', 'strand', 'cds_start_i', 'cds_end_i', 'gene', 'exons'
            ])):
    def __repr__(self):
        return '%s(%s; %d exons)' % (self.__class__, self.ac, len(self.exons))


class Exon(collections.namedtuple('Exon',[
            'start_i', 'end_i', 'name'
            ])):
    def __repr__(self):
        return '%s(%s,%s)' % (self.__class__,self.start_i,self.end_i)
