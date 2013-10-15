import os, sys

from setuptools import setup, find_packages

root_dir = os.path.dirname(__file__)
sys.path[0:0] = [os.path.join(root_dir ,'lib','python')]

with open('doc/description.rst') as f:
    long_description = f.read()

pkg_dir = 'lib/python'
setup(
    author = 'InVitae Keyboard Monkeys',
    author_email='reece@invitae.com',
    license = 'MIT',
    long_description = long_description,
    name = "uta",
    package_dir = {'': pkg_dir},
    packages = find_packages(pkg_dir),
    url = 'https://bitbucket.org/invitae/uta',
    use_hg_version = True,
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
        'hg+ssh://hg@bitbucket.org/locusdevelopment/hgvs@{v}#egg=hgvs-{v}'.format(v='0.0.7'),
    ],

    setup_requires = [
        'hgtools',
        ]
)
