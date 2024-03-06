import unittest
from tempfile import NamedTemporaryFile
import os
import gzip

from sbin.ncbi_parse_genomic_gff import GFFRecord, parse_gff_file, parse_gff_record


class TestGFFParsing(unittest.TestCase):
    def setUp(self):
        with NamedTemporaryFile(suffix='.gz', delete=False) as temp_gff:
            with gzip.open(temp_gff.name, 'wt') as f:
                f.write(
                    "NC_000001.10\tBestRefSeq\texon\t11874\t12227\t.\t+\t.\tID=exon-NR_046018.2-1;Parent=rna-NR_046018.2;transcript_id=NR_046018.2\n")
                f.write(
                    "NC_000001.10\tBestRefSeq\texon\t12613\t12721\t.\t+\t.\tID=exon-NR_046018.2-2;Parent=rna-NR_046018.2;transcript_id=NR_046018.2\n")
                f.write(
                    "NC_000001.10\tBestRefSeq\texon\t13221\t14409\t.\t+\t.\tID=exon-NR_046018.2-3;Parent=rna-NR_046018.2;transcript_id=NR_046018.2\n")
            temp_gff.seek(0)
        self.temp_gff = temp_gff


    def tearDown(self):
        os.remove(self.temp_gff.name)

    def test_parse_gff_record(self):
        # Test parsing a single GFF record
        line = "NC_000001.10\tBestRefSeq\texon\t11874\t12227\t.\t+\t.\tID=exon-NR_046018.2-1;Parent=rna-NR_046018.2;transcript_id=NR_046018.2\n"
        expected_record = GFFRecord(seqid="NC_000001.10", start=11874, end=12227, strand="+", exon_number=1, parent_id="rna-NR_046018.2", transcript_id="NR_046018.2")
        parsed_record = parse_gff_record(line)
        self.assertEqual(parsed_record, expected_record)

    def test_parse_gff_file(self):
        # Test parsing the entire GFF file
        expected_result = {
            "rna-NR_046018.2": [
                GFFRecord(seqid="NC_000001.10", start=11874, end=12227, strand="+", exon_number=1, parent_id="rna-NR_046018.2", transcript_id="NR_046018.2"),
                GFFRecord(seqid="NC_000001.10", start=12613, end=12721, strand="+", exon_number=2, parent_id="rna-NR_046018.2", transcript_id="NR_046018.2"),
                GFFRecord(seqid="NC_000001.10", start=13221, end=14409, strand="+", exon_number=3, parent_id="rna-NR_046018.2", transcript_id="NR_046018.2")
            ]
        }
        parsed_result = parse_gff_file(self.temp_gff.name)
        self.assertEqual(parsed_result, expected_result)


if __name__ == "__main__":
    unittest.main()