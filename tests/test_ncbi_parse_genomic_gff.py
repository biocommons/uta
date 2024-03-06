import subprocess
import unittest
from tempfile import NamedTemporaryFile
import os
import gzip

from sbin.ncbi_parse_genomic_gff import GFFRecord, parse_gff_file, parse_gff_record, get_zero_based_exon_ranges

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)


def sample_line(**params):
    defaults = {
        'seqid': 'NC_000001.10',
        'source': 'BestRefSeq',
        'feature': 'exon',
        'start': 11874,
        'stop': 12227,
        'score': '.',
        'strand': '+',
        'phase': '.',
        'attributes_str': 'ID=exon-NR_046018.2-1;Parent=rna-NR_046018.2;transcript_id=NR_046018.2'
    }
    defaults.update(params)
    return '\t'.join(map(str, defaults.values())) + '\n'


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
        self.gff_records = [
                GFFRecord(seqid="NC_000001.10", start=11874, end=12227, strand="+", exon_number=1, parent_id="rna-NR_046018.2", transcript_id="NR_046018.2"),
                GFFRecord(seqid="NC_000001.10", start=12613, end=12721, strand="+", exon_number=2, parent_id="rna-NR_046018.2", transcript_id="NR_046018.2"),
                GFFRecord(seqid="NC_000001.10", start=13221, end=14409, strand="+", exon_number=3, parent_id="rna-NR_046018.2", transcript_id="NR_046018.2")
            ]

    def tearDown(self):
        os.remove(self.temp_gff.name)

    def test_parse_gff_record(self):
        # Test parsing a single GFF record
        line = sample_line()
        expected_record = GFFRecord(seqid="NC_000001.10", start=11874, end=12227, strand="+", exon_number=1, parent_id="rna-NR_046018.2", transcript_id="NR_046018.2")
        parsed_record = parse_gff_record(line)
        self.assertEqual(parsed_record, expected_record)

    def test_parse_gff_record_skips_non_exon_records(self):
        # We exclude non-exon records
        line = sample_line(feature='pseudogene')
        expected_record = None
        parsed_record = parse_gff_record(line)
        self.assertEqual(parsed_record, expected_record)

    def test_parse_gff_record_skips_non_NC_target(self):
        # We exclude alignments to non-NC chromosomes
        line = sample_line(seqid='NT_123')
        expected_record = None
        parsed_record = parse_gff_record(line)
        self.assertEqual(parsed_record, expected_record)

    def test_parse_gff_record_skips_missing_transcript_id(self):
        # We exclude alignments missing transcript_id
        line = sample_line(attributes_str='ID=exon-NR_046018.2-1;transcript_id=NR_046018.2')  # parent missing from attributes
        expected_record = None
        parsed_record = parse_gff_record(line)
        self.assertEqual(parsed_record, expected_record)

    def test_parse_gff_record_skips_missing_parent_field(self):
        # We exclude alignments missing a parent field
        line = sample_line(attributes_str='ID=exon-NR_046018.2-1;Parent=rna-NR_046018.2')  # transcript_id missing from attributes
        expected_record = None
        parsed_record = parse_gff_record(line)
        self.assertEqual(parsed_record, expected_record)

    def test_parse_gff_record_skips_non_NM_NR_transcripts(self):
        # We only care about transcripts that start with NM_ or NR_
        line = sample_line(attributes_str='ID=exon-NR_046018.2-1;Parent=rna-NR_046018.2;transcript_id=somethingelse')  # transcript_id missing from attributes
        expected_record = None
        parsed_record = parse_gff_record(line)
        self.assertEqual(parsed_record, expected_record)

    def test_parse_gff_record_unexpected_number_of_fields(self):
        # Raise an exception if there are not exactly 9 fields in a non-comment line
        line = "NC_000001.10\tID=exon-NR_046018.2-1;Parent=rna-NR_046018.2;transcript_id=NR_046018\n"  # only 2 fields
        with self.assertRaises(ValueError) as context:
            parse_gff_record(line)

        self.assertEqual(str(context.exception), "Expected 9 tab-separated fields, got 2")

    def test_parse_gff_record_raises_non_int_start_stop(self):
        # Raise an exception if either start or stop is not an integer
        lines = [sample_line(start="a string"), sample_line(stop="another string")]
        for line in lines:
            with self.assertRaises(ValueError):
                parse_gff_record(line)

    def test_parse_gff_record_raises_unparseable_id(self):
        # raise an exception if we cannot parse the exon number from the ID
        line = sample_line(attributes_str='ID=unexpected_id;Parent=rna-NR_046018.2;transcript_id=NR_046018')
        with self.assertRaises(ValueError) as context:
            parse_gff_record(line)

        self.assertEqual(str(context.exception), "Failed to parse exon number from unexpected_id")

    def test_parse_gff_file(self):
        # Test parsing the entire GFF file
        expected_result = {
            "rna-NR_046018.2": self.gff_records
        }
        parsed_result = parse_gff_file(self.temp_gff.name)
        self.assertEqual(parsed_result, expected_result)

    def test_get_zero_based_exon_ranges(self):
        # Test converting exon ranges to 0-based half-open format yields expected values
        exon_ranges = get_zero_based_exon_ranges(self.gff_records)
        assert exon_ranges == "11873,12227;12612,12721;13220,14409"

    def test_script_output(self):
        # Run the script from the command line
        file_prefix = 'genomic_100'
        input_gff_file = os.path.join(CURRENT_DIR, 'data', f'{file_prefix}.gff.gz')

        script_path = os.path.join(BASE_DIR, 'sbin', 'ncbi_parse_genomic_gff.py')
        expected_output_file = os.path.join(CURRENT_DIR, 'data', f'expected_{file_prefix}.exonset.gz')
        output_file = os.path.join(os.getcwd(), f'{file_prefix}.exonset.gz')

        command = ['python', script_path, input_gff_file, '--prefix', file_prefix]
        subprocess.run(command, check=True)

        # Compare the generated output file with the expected file
        self.assertTrue(os.path.isfile(output_file), "Output file not generated.")
        with gzip.open(expected_output_file, 'rb') as expected_file, gzip.open(output_file, 'rb') as actual_file:
            expected_content = expected_file.read()
            actual_content = actual_file.read()
            self.assertEqual(expected_content, actual_content, "Output file content doesn't match expected.")

        # Clean up temporary files if needed
        os.remove(output_file)


if __name__ == "__main__":
    unittest.main()