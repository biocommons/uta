import csv
import recordtype

class ExonSet( recordtype.recordtype('ExonSet',
                                     ['tx_ac','alt_ac','method','strand','exons_se_i']) ):
    pass

class ExonSetWriter(csv.DictWriter):
    def __init__(self,tsvfile):
        csv.DictWriter.__init__(self,tsvfile, fieldnames=ExonSet._fields, delimiter=b'\t', lineterminator="\n")
        csv.DictWriter.writeheader(self)
        
    def write(self,si):
        self.writerow(si._asdict())

class ExonSetReader(csv.DictReader):
    def __init__(self,tsvfile):
        csv.DictReader.__init__(self,tsvfile,delimiter=b'\t')
        if set(self.fieldnames) != set(ExonSet._fields):
            raise RuntimeError('Format error: expected header with these columns: '+','.join(ExonSet._fields) + " but got: "+','.join(self.fieldnames))

    def next(self):
        d = csv.DictReader.next(self)
        return ExonSet(**d)



if __name__ == '__main__':
    tmpfn = '/tmp/exonset'

    with open(tmpfn,'w') as f:
        esw = ExonSetWriter(f)
        for i in range(3):
            es = ExonSet(**dict([(k,k+":"+str(i)) for k in ExonSet._fields]))
            esw.write(es)


    with open(tmpfn,'r') as f:
        esr = ExonSetReader(f)
        for es in esr:
            print(es)
