import contextlib
import io
import sys
import unittest
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from sbin.coalesce_exonsets import coalesce_exonsets
from uta.formats.exonset import ExonSetWriter


class TestCoalesceExonsets(unittest.TestCase):

    def _create_temporary_file(self, lines):
        with NamedTemporaryFile(delete=False) as temp_exonsets:
            with open(temp_exonsets.name, "wt") as f:
                for line in lines:
                    f.write(line)
            temp_exonsets.seek(0)
        return temp_exonsets.name

    @patch('sbin.coalesce_exonsets.logger')
    def test_coalesce_exonsets(self, mock_logger):
        lines_1 = [
            "tx_ac\talt_ac\tmethod\tstrand\texons_se_i\n",
            "NM_145660.2\tNC_000022.10\tsplign\t-1\t36600673,36600879;36598038,36598101;36595375,36595422;36591356,36591483;36585175,36587958\n",
            "NM_000348.4\tNC_000002.11\tsplign\t-1\t31805689,31806007;31758672,31758836;31756440,31756542;31754376,31754527;31747549,31751332\n"
        ]
        lines_2 = [
            "tx_ac\talt_ac\tmethod\tstrand\texons_se_i\n",
            "NM_145660.2\tNC_000022.10\tsplign\t-1\t36600673,36600879;36598038,36598101;36595375,36595422;36591356,36591483;36587846,36587958;36585175,36587845\n",
            "NM_145660.2\tNC_000022.11\tsplign\t-1\t36204627,36204833;36201992,36202055;36199329,36199376;36195310,36195437;36189127,36191912\n",
            "NM_001005484.2\tNC_000001.10\tsplign\t1\t65418,65433;65519,65573;69036,71585\n"
        ]
        temp_exonsets_1_fn = self._create_temporary_file(lines_1)
        temp_exonsets_2_fn = self._create_temporary_file(lines_2)

        # the first record in lines_2 (NM_145660.2, NC_000022.10) will be skipped, as it is already passed to the output
        expected_output = lines_1 + lines_2[2:]
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            coalesce_exonsets([temp_exonsets_1_fn, temp_exonsets_2_fn])

        output = stdout.getvalue()
        self.assertEqual(output, ''.join(expected_output))

        mock_logger.warning.assert_called_with(f"  - exon set for transcript NM_145660.2/NC_000022.10 already seen in {temp_exonsets_1_fn}. Skipping.")
