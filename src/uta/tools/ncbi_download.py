# Step 1 in the new uta-light update
# download all files that are needed from the NCBI website

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from uta.enumerations import chrMT
from uta.config.config import get_config


# TODO: download the mito genbank file and fasta file.
# for now download Genbank record and fasta from https://www.ncbi.nlm.nih.gov/nuccore/NC_012920.1


class NCBIDownloader:
    def __init__(self):
        self.config = get_config()

    def _get_files_to_download(self):
        """reads file names from config file and returns URLs."""
        files = []
        hostname = self.config.get("global", "ncbi_host")

        for section in self.config.sections():
            if section == "global":
                continue

            bam = self.config.get(section, "bam")
            bai = bam + ".bai"
            gtf = self.config.get(section, "gtf")
            gbff = self.config.get(section, "gbff")

            for f in [bam, bai, gtf, gbff]:
                url = hostname + f
                if not self._exists_locally(url):
                    files.append(url)

        return files

    def get_local_files(self, file_type: str, section: Optional[str] = None):
        """Returns a list of local files of a specific type, e.g. bam or gtf"""

        local_files = []
        for s in self.config.sections():
            if s == "global":
                continue
            if section is not None and s != section:
                continue

            url_str = self.config.get(s, file_type)
            p = self._get_local_path(url_str)
            local_files.append((s, p))
        return local_files

    def _exists_locally(self, url_str):
        """check if a file has been"""
        p = self._get_local_path(url_str)
        return p.exists()

    def get_local_folder(self):
        folder = self.config.get("global", "download_folder")
        return Path(folder)

    def _get_local_path(self, url_str):
        """Returns the local path that is the mirror of the remote url."""
        folder = self.config.get("global", "download_folder")
        filename = self._get_filename(url_str)

        p = Path(folder + filename)
        return p

    def _get_filename(self, url_str):
        """returns the last part of the URL assuming it is a filename"""

        a = urlparse(url_str)
        return os.path.basename(a.path)

    def _download(self, url_str: str):
        destination_file = self._get_filename(url_str)

        local_path = self._get_local_path(url_str)
        self._download_to(url_str, local_path)

    def _download_to(self, url_str, local_path):
        print(f"downloading {url_str} to {local_path}")

        # get total:
        response = requests.get(url_str, stream=True)
        resp_headers = response.headers
        total = -1
        if "content-length" in resp_headers:
            total = int(resp_headers["content-length"])

        with open(local_path, "wb") as handle:
            for data in tqdm(
                response.iter_content(),
                total=total,
                bar_format="{l_bar}{bar:10}{r_bar}{bar:-10b}",
            ):
                handle.write(data)

    def update(self):
        """Check files if they are available locally, and if not, download them."""

        files = self._get_files_to_download()
        for file in files:
            self._download(file)

    def check_download_mito(self, files):
        all_files_exist = True
        for file in files:
            if not file.exists():
                all_files_exist = False
                break

        if all_files_exist:
            # don't need to download
            return

        genbank_local = files[0]
        fasta_local = files[1]

        genbank_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={chrMT}&retmode=text&rettype=gb"
        fasta_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={chrMT}&retmode=text&rettype=fasta"

        self._download_to(genbank_url, genbank_local)
        self._download_to(fasta_url, fasta_local)
