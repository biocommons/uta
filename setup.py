import os
import sys

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

# full path appears to be required for old (0.6.x?) versions of setuptools
root_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(root_dir, 'doc/description.rst')) as f:
    long_description = f.read()

pkg_dir = 'lib/python'
setup(
    author = 'InVitae Keyboard Monkeys',
    license = 'MIT',
    long_description = long_description,
    use_hg_version = True,
    zip_safe = True,

    author_email='reece+uta@invitae.com',
    description='Universal Transcript Archive',
    name = "uta",
    package_dir = {'': pkg_dir},
    packages = find_packages(pkg_dir),
    url = 'https://bitbucket.org/invitae/uta',


    install_requires = [
        'nose',
        'sphinx',
        'sphinx-pypi-upload',
        'sphinx_rtd_theme',
        'sphinxcontrib-httpdomain',

        'docopt',
        'psycopg2',
        'sqlalchemy',
        ],

    setup_requires = [
        'hgtools',
        ],
)
