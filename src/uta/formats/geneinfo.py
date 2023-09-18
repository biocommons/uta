import csv
import recordtype

default_sep = ','


class GeneInfo(recordtype.recordtype('GeneInfo',
                                     ['gene_id', 'tax_id', 'hgnc', 'maploc', 'aliases', 'type', 'summary', 'descr', 'xrefs'])):
    pass


class GeneInfoWriter(csv.DictWriter):

    def __init__(self, tsvfile):
        csv.DictWriter.__init__(
            self, tsvfile, fieldnames=GeneInfo._fields, delimiter='\t', lineterminator="\n")
        csv.DictWriter.writeheader(self)

    def write(self, si):
        d = si._asdict()
        d['aliases'] = default_sep.join(d['aliases'])
        d['xrefs'] = default_sep.join(d['xrefs'])
        self.writerow(d)


class GeneInfoReader(csv.DictReader):

    def __init__(self, tsvfile):
        csv.DictReader.__init__(self, tsvfile, delimiter='\t')
        if set(self.fieldnames) != set(GeneInfo._fields):
            raise RuntimeError('Format error: expected header with these columns: ' +
                               ','.join(GeneInfo._fields) + " but got: " + ','.join(self.fieldnames))

    def __next__(self):
        d = super().__next__()
        d['aliases'] = d['aliases'].split(default_sep)
        d['xrefs'] = d['xrefs'].split(default_sep)
        return GeneInfo(**d)



if __name__ == '__main__':
    tmpfn = '/tmp/exonset'

    with open(tmpfn, 'w') as f:
        esw = GeneInfoWriter(f)
        for i in range(3):
            es = GeneInfo(
                **dict([(k, k + ":" + str(i)) for k in GeneInfo._fields]))
            esw.write(es)

    with open(tmpfn, 'r') as f:
        esr = GeneInfoReader(f)
        for es in esr:
            print(es)
