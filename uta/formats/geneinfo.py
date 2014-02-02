import csv
import recordtype

class GeneInfo( recordtype.recordtype('GeneInfo',
                                     ['hgnc','maploc','aliases','type','summary','descr']) ):
    pass

class GeneInfoWriter(csv.DictWriter):
    def __init__(self,tsvfile):
        csv.DictWriter.__init__(self,tsvfile, fieldnames=GeneInfo._fields, delimiter=b'\t')
        csv.DictWriter.writeheader(self)
        
    def write(self,si):
        self.writerow(si._asdict())

class GeneInfoReader(csv.DictReader):
    def __init__(self,tsvfile):
        csv.DictReader.__init__(self,tsvfile,delimiter=b'\t')
        if set(self.fieldnames) != set(GeneInfo._fields):
            raise RuntimeError('Format error: expected header with these columns: '+','.join(GeneInfo._fields) + " but got: "+','.join(self.fieldnames))

    def next(self):
        d = csv.DictReader.next(self)
        return GeneInfo(**d)



if __name__ == '__main__':
    tmpfn = '/tmp/exonset'

    with open(tmpfn,'w') as f:
        esw = GeneInfoWriter(f)
        for i in range(3):
            es = GeneInfo(**dict([(k,k+":"+str(i)) for k in GeneInfo._fields]))
            esw.write(es)


    with open(tmpfn,'r') as f:
        esr = GeneInfoReader(f)
        for es in esr:
            print(es)
