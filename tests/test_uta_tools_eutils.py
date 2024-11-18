import os
import unittest
from unittest.mock import Mock, patch

from uta import EutilsDownloadError
from uta.tools.eutils import download_from_eutils, NcbiFileFormatEnum


class TestEutils(unittest.TestCase):
    URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'

    def setUp(self):
        self.output_file = 'test_output.fa'

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    @patch('requests.get')
    def test_successful_download(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'file content'
        mock_get.return_value = mock_response

        download_from_eutils('accession', NcbiFileFormatEnum.FASTA, self.output_file)

        mock_get.assert_called_once_with(
            self.URL,
            params={
                'db': 'nuccore',
                'id': 'accession',
                'retmode': 'text',
                'rettype': 'fasta'
            }
        )

        with open(self.output_file, 'r') as file:
            self.assertEqual(file.read(), 'file content')

    @patch('requests.get')
    def test_unsuccessful_download(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        with self.assertRaises(EutilsDownloadError):
            download_from_eutils('accession', NcbiFileFormatEnum.FASTA, self.output_file)
