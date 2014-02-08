import csv
import recordtype

class SeqInfo( recordtype.recordtype('SeqInfo', ['md5','origin','ac','descr','len','seq']) ):
    pass

class SeqInfoWriter(csv.DictWriter):
    def __init__(self,tsvfile):
        csv.DictWriter.__init__(self,tsvfile, fieldnames=SeqInfo._fields, delimiter=b'\t')
        csv.DictWriter.writeheader(self)
        
    def write(self,si):
        self.writerow(si._asdict())

class SeqInfoReader(csv.DictReader):
    def __init__(self,tsvfile):
        csv.DictReader.__init__(self,tsvfile,delimiter=b'\t')
        if set(self.fieldnames) != set(SeqInfo._fields):
            raise RuntimeError('Format error: expected header with these columns: '+','.join(SeqInfo._fields) + " but got: "+','.join(self.fieldnames))

    def next(self):
        d = csv.DictReader.next(self)
        si = SeqInfo(**d)
        if si.seq == '':
            si.seq = None
        return si


if __name__ == '__main__':

    tmpfn = '/tmp/seqinfo.tsv'

    with open(tmpfn,'w') as f:
        siw = SeqInfoWriter(f)
        for i in range(3):
            si = SeqInfo(md5='md5:'+str(i),origin='origin:'+str(i),ac='ac:'+str(i),descr='descr:'+str(i),seq='seq:'+str(i))
            siw.write(si)


    with open(tmpfn,'r') as f:
        sir = SeqInfoReader(f)
        for si in sir:
            print(si)
