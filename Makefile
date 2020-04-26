# Makefile for Python project

.DELETE_ON_ERROR:
.PHONY: FORCE
.PRECIOUS:
.SUFFIXES :

SHELL:=/bin/bash -e -o pipefail
SELF:=$(firstword $(MAKEFILE_LIST))

PKG=bioutils
PKGD=$(subst .,/,${PKG})

PYV=3.7
VEDIR=venv/${PYV}

#UTA_DB_URL=postgresql://uta_public:uta_public@uta.invitae.com/uta/uta_20140210
#UTA_DB_URL=postgresql://localhost/uta/uta_20140210
#UTA_DB_URL=postgresql://localhost/uta_dev/uta_20140210
#UTA_DB_URL=sqlite:///tmp/uta-0.0.5.db

############################################################################
#= BASIC USAGE
default: help

#=> help -- display this help message
help:
	@sbin/makefile-extract-documentation "${SELF}"

config:
	@echo CONFIGURATION
	@echo "  UTA_DB_URL=${UTA_DB_URL}"


############################################################################
#= SETUP, INSTALLATION, PACKAGING

#=> devready: create venv and install pkg in develop mode
.PHONY: devready
devready:
	make ${VEDIR} && source ${VEDIR}/bin/activate && make develop
	@echo '#################################################################################'
	@echo '###  Do not forget to `source ${VEDIR}/bin/activate` to use this environment  ###'
	@echo '#################################################################################'

#=> venv: make a Python 3 virtual environment
venv/3 venv/3.5 venv/3.6 venv/3.7: venv/%:
	python$* -mvenv $@; \
	source $@/bin/activate; \
	python -m ensurepip --upgrade; \
	pip install --upgrade pip setuptools

#=> develop: install package in develop mode
develop:
	pip install -e .[dev]

#=> install: install package
#=> bdist bdist_egg bdist_wheel build sdist: distribution options
.PHONY: bdist bdist_egg bdist_wheel build build_sphinx sdist install
bdist bdist_egg bdist_wheel build sdist install: %:
	python setup.py $@

bdist bdist_egg build build_sphinx install sdist: %:
	python setup.py $*

#=> upload
upload: upload_pypi

#=> upload_all: upload_pypi, upload_invitae, and upload_docs
upload_all: upload_pypi upload_docs

#=> upload_*: upload to named pypi service (requires config in ~/.pypirc)
upload_%:
	python setup.py bdist_egg sdist upload -r $*

#=> upload_docs: upload documentation to pythonhosted
upload_docs: %:
	python setup.py $* -r pypi


############################################################################
#= TESTING

#=> test -- run tests
test-setup: develop

#=> test, test-with-coverage -- per-commit test target for CI
# see test configuration in setup.cfg
test test-with-coverage:
	python setup.py nosetests

#=> ci-test -- per-commit test target for CI
ci-test: test

#=> ci-test-ve -- test in virtualenv
ci-test-ve: ve
	source ve/bin/activate; \
	make ci-test



############################################################################
#= UTILITY TARGETS

# N.B. Although code is stored in github, I use hg and hg-git on the command line
#=> reformat: reformat code with yapf and commit
.PHONY: reformat
reformat:
	@if hg sum | grep -qL '^commit:.*modified'; then echo "Repository not clean" 1>&2; exit 1; fi
	@if hg sum | grep -qL ' applied'; then echo "Repository has applied patches" 1>&2; exit 1; fi
	yapf -i -r "${PKGD}" tests
	hg commit -m "reformatted with yapf"

#=> changelog
doc/source/changelog.rst: CHANGELOG
	clog-txt-to-rst <$< >$@

#=> lint -- run lint, flake, etc
# TBD

#=> docs-aux -- make generated docs for sphinx
docs-aux:
	make -C misc/railroad doc-install
	make -C examples doc-install

############################################################################
#= CLEANUP

#=> clean: remove temporary and backup files
.PHONY: clean
clean:
	find . \( -name \*~ -o -name \*.bak \) -print0 | xargs -0r rm

#=> cleaner: remove files and directories that are easily rebuilt
.PHONY: cleaner
cleaner: clean
	rm -fr .cache *.egg-info build dist doc/_build htmlcov
	find . \( -name \*.pyc -o -name \*.orig -o -name \*.rej \) -print0 | xargs -0r rm
	find . -name __pycache__ -print0 | xargs -0r rm -fr

#=> cleanest: remove files and directories that require more time/network fetches to rebuild
.PHONY: cleanest
cleanest: cleaner
	rm -fr .eggs .tox venv


## <LICENSE>
## Copyright 2016 Source Code Committers
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
