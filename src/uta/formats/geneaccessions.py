import csv
import recordtype


class GeneAccessions(recordtype.recordtype('GeneAccessions',
                                           ['gene_symbol', 'tx_ac', 'gene_id', 'pro_ac', 'origin'])):
    pass


class GeneAccessionsWriter(csv.DictWriter):

    def __init__(self, tsvfile):
        csv.DictWriter.__init__(
            self, tsvfile, fieldnames=GeneAccessions._fields, delimiter='\t', lineterminator="\n")
        csv.DictWriter.writeheader(self)

    def write(self, si):
        self.writerow(si._asdict())


class GeneAccessionsReader(csv.DictReader):

    def __init__(self, tsvfile):
        csv.DictReader.__init__(self, tsvfile, delimiter='\t')
        if set(self.fieldnames) != set(GeneAccessions._fields):
            raise RuntimeError('Format error: expected header with these columns: ' + ','.join(
                GeneAccessions._fields) + " but got: " + ','.join(self.fieldnames))

    def __next__(self):
        d = super().__next__()
        return GeneAccessions(**d)


if __name__ == '__main__':
    tmpfn = '/tmp/geneacs'

    with open(tmpfn, 'w') as f:
        esw = GeneAccessionsWriter(f)
        for i in range(3):
            es = GeneAccessions(
                **dict([(k, k + ":" + str(i)) for k in GeneAccessions._fields]))
            esw.write(es)

    with open(tmpfn, 'r') as f:
        esr = GeneAccessionsReader(f)
        for es in esr:
            print(es)
