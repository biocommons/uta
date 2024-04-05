import contextlib
import io
import unittest
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from sbin.filter_exonset_transcripts import filter_exonset


class TestFilterExonsetTranscripts(unittest.TestCase):

    @patch('sbin.filter_exonset_transcripts.logger')
    def test_filter_exonset(self, mock_logger):
        # Test NR_046571.1 is filtered out
        lines = [
            "tx_ac\talt_ac\tmethod\tstrand\texons_se_i\n",
            "NR_122113.1\tNC_000022.10\tsplign\t-1\t16192905,16193009;16190680,16190791;16189263,16189378;16189031,16189143;16187164,16187302;16186810,16186953;16162396,16162487;16150528,16151821\n",
            "NR_133911.1\tNC_000022.10\tsplign\t1\t16157078,16157342;16164481,16164569;16171951,16172265\n",
            "NR_046571.1\tNC_000022.10\tsplign\t1\t16274608,16275003;16276480,16277577\n"
        ]
        with NamedTemporaryFile(delete=False) as temp_exonsets:
            with open(temp_exonsets.name, "wt") as f:
                for line in lines:
                    f.write(line)
            temp_exonsets.seek(0)
        missing_ids_file = NamedTemporaryFile()

        transcript_ids = {"NR_122113.1", "NR_133911.1"}
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            filter_exonset(temp_exonsets.name, transcript_ids, missing_ids_file.name)

        # Assert the record for NR_046571.1 is filtered out
        self.assertEqual(stdout.getvalue(), ''.join(lines[0:3]))

        # Confirm filtered transcript is present in missing_ids_file
        with open(missing_ids_file.name, 'r') as f:
            contents = f.read()
        self.assertEqual(contents, 'NR_046571.1\n')

        mock_logger.warning.assert_called_with('Exon set transcript NR_046571.1 not found in txinfo file. Filtering out.')
        mock_logger.info.assert_called_with('Filtered out exon sets for 1 transcript(s): NR_046571.1')


if __name__ == "__main__":
    unittest.main()
