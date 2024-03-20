import csv
import recordtype


class TxInfo(recordtype.recordtype('TxInfo',
                                   ['origin', 'ac', 'gene_id', 'gene_symbol', 'cds_se_i', 'exons_se_i'])):
    pass


class TxInfoWriter(csv.DictWriter):

    def __init__(self, tsvfile):
        csv.DictWriter.__init__(
            self, tsvfile, fieldnames=TxInfo._fields, delimiter='\t', lineterminator="\n")
        csv.DictWriter.writeheader(self)

    def write(self, si):
        self.writerow(si._asdict())


class TxInfoReader(csv.DictReader):

    def __init__(self, tsvfile):
        csv.DictReader.__init__(self, tsvfile, delimiter='\t')
        if set(self.fieldnames) != set(TxInfo._fields):
            raise RuntimeError('Format error: expected header with these columns: '
                               + ', '.join(TxInfo._fields) + " but got: " + ', '.join(self.fieldnames))

    def __next__(self):
        d = super().__next__()
        return TxInfo(**d)


if __name__ == '__main__':
    tmpfn = '/tmp/txinfo'

    with open(tmpfn, 'w') as f:
        esw = TxInfoWriter(f)
        for i in range(3):
            es = TxInfo(**dict([(k, k + ":" + str(i))
                                for k in TxInfo._fields]))
            esw.write(es)

    with open(tmpfn, 'r') as f:
        esr = TxInfoReader(f)
        for es in esr:
            print(es)
