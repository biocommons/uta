import csv, io

from uta.exceptions import *

class GeneInfoParser(object):
    """Parse gene_info.gz files as from ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz"""
    def __init__(self,fh):
        self._fh = fh
        header = self._fh.next().rstrip()
        if header != '#Format: tax_id GeneID Symbol LocusTag Synonyms dbXrefs chromosome map_location description type_of_gene Symbol_from_nomenclature_authority Full_name_from_nomenclature_authority Nomenclature_status Other_designations Modification_date (tab is used as a separator, pound sign - start of a comment)':
            raise UTAError("""gene info doesn't contain expected header; got:\n{header}""".format(
                    header=header))
        fields = header.replace('#Format: ','').replace(' (tab is used as a separator, pound sign - start of a comment)','').split(' ')
        self._csvreader = csv.DictReader(self._fh, fieldnames = fields, delimiter = '\t')

    def __iter__(self):
        return self

    def next(self):
        return self._csvreader.next()

## <LICENSE>
## Copyright 2014 UTA Contributors (https://bitbucket.org/invitae/uta)
## 
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
## 
##     http://www.apache.org/licenses/LICENSE-2.0
## 
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## </LICENSE>
