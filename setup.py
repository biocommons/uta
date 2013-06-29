from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

# fetch __version__
with open('lib/python/uta/version.py') as f: exec(f.read())

setup(
    author = 'InVitae Keyboard Monkeys',
    author_email='reece.hart@invitae.com',   # TODO: ask devs about gen. support address
    description = """Universal Transcript Archive""",
    license = 'MIT',
    name = "UTA",
    packages = find_packages(),
    url = 'https://bitbucket.org/invitae/uta',
    version = __version__,
    zip_safe = True,
    install_requires = [
        # 'alembic'
        # 'biopython',
        'docopt',
        'nose',
        'prettytable',
        'psycopg2',
        'sphinx',
        'sqlalchemy',
        ],    
)
