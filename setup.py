from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

setup(
    license = "Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)",
    long_description = long_description,
    use_scm_version = True,
    zip_safe = True,

    author="UTA Contributors",
    author_email="reecehart+uta@gmail.com",
    description="Universal Transcript Archive",
    name="uta",
    packages=find_packages(),
    url="https://github.com/biocommons/uta",

    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Database :: Front-Ends",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],

    keywords = [
        "bioinformatics",
        "computational biology",
        "genome variants",
        "genome variation",
        "genomic variants",
        "genomic variation",
        "genomics",
        "hgvs",
    ],

    entry_points = {
        "console_scripts": [
            "uta = uta.cli:main",
        ],
    },

    install_requires=[
        "attrs",
        "biocommons.seqrepo",
        "biopython>=1.69",
        "bioutils",
        "colorlog",
        "configparser",
        "docopt",
        "eutils>=0.3.2",
        "nose",
        "prettytable",
        "psycopg2-binary",
        "pytz",
        "recordtype",
        "sqlalchemy",
        "uta-align",
    ],

    setup_requires = [
        "nose",
        "setuptools_scm==1.11.1",
        "wheel",
    ],

    tests_require=[
        "coverage",
        "testing.postgresql",
        "wheel",                # to suppress warnings from build env
    ],
)

# <LICENSE>
# Copyright 2021 UTA Contributors (https://github.com/biocommons/uta)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# </LICENSE>
