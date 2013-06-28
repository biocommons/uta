from uta.tools.transcriptmapper import TranscriptMapper

class TranscriptProjector(object):
    def __init__(self,db,ref,from_ac,to_ac):
        self.db = db
        self.ref = ref
        self.from_tm = TranscriptMapper(db,from_ac,ref)
        self.to_tm = TranscriptMapper(db,to_ac,ref)

    def map_forward(self,start_i,end_i):
        return self.to_tm.g_to_c( *self.from_tm.c_to_g(start_i,end_i) )
        
    def map_backward(self,start_i,end_i):
        return self.from_tm.g_to_c( *self.to_tm.c_to_g(start_i,end_i) )
    
