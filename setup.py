from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "UTA",
    description = """Universal Transcript Archive""",
    license = 'MIT',
    version = "0.0.0",
    author_email='reece.hart@invitae.com',
    packages = find_packages(),
    zip_safe = True,
    #test_suite = 'nose.collector',
    install_requires = [
        'nose',
        'sqlalchemy',
        ],    
)
