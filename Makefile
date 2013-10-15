# UTA -- Universal Transcript Archive Makefile
# https://bitbucket.org/invitae/uta

.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail
SELF:=$(firstword $(MAKEFILE_LIST))
export PYTHONPATH=lib/python

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

#=> setup -- prepare python and perl environment for prequisites
#=>> This is optional; the only requirement is that packages are discoverable
#=>> in PYTHONPATH and PERL5LIB
setup: setup-perl   # setup-python 

#=> setup-python: create a virtualenv with base packages
# NOTE: setup-python only makes the virtualenv. You must actvate it
# yourself (source ve/bin/activate)
setup-python: ve
	source ve/bin/activate; python setup.py develop
ve: virtualenv.py
	python $< --distribute ve
virtualenv.py:
	curl https://raw.github.com/pypa/virtualenv/master/virtualenv.py >$@

#=> setup-perl: install perl packages
# TODO: consider perl brew instead
setup-perl:
	./sbin/perl-module-install --install-base ve   Log::Log4perl


############################################################################
#= UTILITY FUNCTIONS

#=> lint -- run lint
# TBD

#=> test -- run tests
test:
	PYTHONPATH=lib/python nosetests --with-xunit

#=> docs -- make sphinx docs
docs: build_sphinx

#=> develop, build_sphinx, sdist, upload_sphinx
build build_sphinx develop install sdist upload_sphinx: %:
	python setup.py $*

#=> upload-<tag>
upload-%:
	[ -z "$$(hg st -admnr)" ] || { echo "Directory contains changes; aborting." 1>&2; hg st -admr; exit 1; }
	R=$$(hg id -t); hg up -r $*; python setup.py sdist upload ${PYPI_SERVICE}; hg up -r $$R


############################################################################
#= CLEANUP
.PHONY: clean cleaner cleanest pristine
#=> clean: clean up editor backups, etc.
clean:
	find . -name \*~ -print0 | xargs -0r /bin/rm
#=> cleaner: above, and remove generated files
cleaner: clean
	find . -name \*.pyc -print0 | xargs -0r /bin/rm -f
	/bin/rm -fr distribute-* *.egg *.egg-info nosetests.xml
	/bin/rm -fr .uta.conf.mk
	make -C doc clean
#=> cleanest: above, and remove the virtualenv, .orig, and .bak files
cleanest: cleaner
	find . \( -name \*.orig -o -name \*.bak \) -print0 | xargs -0r /bin/rm -v
	/bin/rm -fr build bdist dist sdist ve
#=> pristine: above, and delete anything unknown to mercurial
pristine: cleanest
	hg st -un0 | xargs -0r echo /bin/rm -fv
