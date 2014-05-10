import os
import sys

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

with open('doc/description.txt') as f:
    long_description = f.read()

def version_handler(mgr, options):
    version = mgr.get_current_version()
    if version.endswith('dev'):
        version += '-' + mgr._invoke('log','-l1','-r.','--template','{node|short}').strip()
    return version

setup(
    license = 'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)',
    long_description = long_description,
    use_vcs_version = {'version_handler': version_handler},
    zip_safe = True,

    author = 'UTA Contributors',
    author_email='reecehart+uta@gmail.com',
    description='Universal Transcript Archive',
    name = "uta",
    packages = find_packages(),
    url = 'https://bitbucket.org/invitae/uta',

    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python",
        "Topic :: Database :: Front-Ends",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        ],

    keywords = [
        'bioinformatics',
        'computational biology',
        'genome variants',
        'genome variation',
        'genomic variants',
        'genomic variation',
        'genomics',
        'hgvs',
        ],

    install_requires = [
        'biopython',
        'colorlog',
        'docopt',
        'eutils',
        'nose',
        'psycopg2',
        'pytz',
        'recordtype',
        'sqlalchemy',
        ],

    setup_requires = [
        'hgtools',
        'nose',
        'sphinx',
        'sphinxcontrib-fulltoc',
        ],

    tests_require = [
        'coverage',
        'testing.postgresql',
        ],
)

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
