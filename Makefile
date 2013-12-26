.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail
SELF:=$(firstword $(MAKEFILE_LIST))

export PYTHONPATH=lib/python

ifdef LOCAL_UTA
export UTA_DB_URL=postgresql://localhost/uta
endif

PYPI_SERVICE:=-r invitae

# make config in etc/uta.conf available within the Makefile
-include .uta.conf.mk
.uta.conf.mk: etc/uta.conf
	./sbin/conf-to-vars $< >$@

############################################################################
#= BASIC USAGE
default: help

#=> help -- display this help message
help:
	@sbin/extract-makefile-documentation "${SELF}"

############################################################################
#= INSTALLATION/SETUP

#=> ve -- create a virtualenv
VE_DIR:=ve
VE_MAJOR:=1
VE_MINOR:=10
VE_PY_DIR:=virtualenv-${VE_MAJOR}.${VE_MINOR}
VE_PY:=${VE_PY_DIR}/virtualenv.py
${VE_PY}:
	curl -sO  https://pypi.python.org/packages/source/v/virtualenv/virtualenv-${VE_MAJOR}.${VE_MINOR}.tar.gz
	tar -xvzf virtualenv-${VE_MAJOR}.${VE_MINOR}.tar.gz
	rm -f virtualenv-${VE_MAJOR}.${VE_MINOR}.tar.gz
${VE_DIR}: ${VE_PY} 
	${SYSTEM_PYTHON} $< ${VE_DIR} 2>&1 | tee "$@.err"
	/bin/mv "$@.err" "$@"


#=> setup -- prepare python and perl environment for prequisites
#=>> This is optional; the only requirement is that packages are discoverable
#=>> in PYTHONPATH and PERL5LIB
setup: setup-perl   # setup-python 

#=> setup-python: run python setup.py
setup-python:
	python setup.py develop

#=> setup-perl: install perl packages
# TODO: consider perl brew instead
setup-perl:
	./sbin/perl-module-install --install-base ve   Log::Log4perl


############################################################################
#= UTILITY FUNCTIONS

#=> develop, build_sphinx, sdist, upload_sphinx
bdist bdist_egg build build_sphinx develop install sdist upload_sphinx: %:
	python setup.py $*

#=> test -- run tests
test:
	nosetests --with-xunit

#=> lint -- run lint, flake, etc
# TBD

#=> docs -- make sphinx docs
docs: build_sphinx

#=> continuous integration tests -- target for jenkins (and now travis, drone, or other providers)
ci-test jenkins:
	make ve \
	&& source ve/bin/activate \
	&& make install \
	&& make test \
	&& make docs

#=> upload-<tag>
upload-%:
	[ -z "$$(hg st -admnr)" ] || { echo "Directory contains changes; aborting." 1>&2; hg st -admr; exit 1; }
	R=$$(hg id -t); hg up -r $*; python setup.py sdist upload ${PYPI_SERVICE}; hg up -r $$R

#=> upload
upload:
	python setup.py bdist bdist_egg sdist upload ${PYPI_SERVICE}


############################################################################
#= CLEANUP
.PHONY: clean cleaner cleanest pristine
#=> clean: clean up editor backups, etc.
clean:
	find . -name \*~ -print0 | xargs -0r /bin/rm
#=> cleaner: above, and remove generated files
cleaner: clean
	find . -name \*.pyc -print0 | xargs -0r /bin/rm -f
	/bin/rm -fr distribute-* *.egg *.egg-info *.tar.gz nosetests.xml
	/bin/rm -fr .uta.conf.mk
	make -C doc clean
#=> cleanest: above, and remove the virtualenv, .orig, and .bak files
cleanest: cleaner
	find . \( -name \*.orig -o -name \*.bak \) -print0 | xargs -0r /bin/rm -v
	/bin/rm -fr build bdist dist sdist ve virtualenv*
#=> pristine: above, and delete anything unknown to mercurial
pristine: cleanest
	hg st -un0 | xargs -0r echo /bin/rm -fv
