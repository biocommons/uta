import os, sys

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

root_dir = os.path.dirname(__file__)
sys.path[0:0] = [os.path.join(root_dir ,'lib','python')]

# fetch __version__
with open('lib/python/uta/version.py') as f:
    exec(f.read())

with open('doc/description.rst') as f:
    long_description = f.read()

pkg_dir = 'lib/python'
setup(
    author = 'InVitae Keyboard Monkeys',
    author_email='reece.hart@invitae.com',   # TODO: ask devs about gen. support address
    description = """Universal Transcript Archive""",
    license = 'MIT',
    long_description = long_description,
    name = "UTA",
    package_dir = {'': pkg_dir},
    packages = find_packages(pkg_dir),
    url = 'https://bitbucket.org/invitae/uta',
    version = __version__,
    zip_safe = True,
    install_requires = [
        'docopt',
        'hgvs',
        'nose',
        'prettytable',
        'psycopg2',
        'sphinx',
        'sphinx-pypi-upload',
        'sqlalchemy',
        ],
    dependency_links = [
        'hg+ssh://hg@bitbucket.org/locusdevelopment/hgvs@0.0.2#egg=hgvs-0.0.2',
    ],
)


