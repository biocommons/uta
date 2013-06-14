import unittest

import sqlalchemy as sa
import sqlalchemy.orm as sao
import sqlalchemy.ext.declarative as saed

import uta.sa_models as usam

class Test_uta_sa_models(unittest.TestCase):
    def test_load(self):
        engine = sa.create_engine('sqlite:///:memory:')

        usam.Base.metadata.create_all(engine) 

        Session = sao.sessionmaker(bind=engine)
        session = Session()

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

        
        



if __name__ == '__main__':
    unittest.main()
