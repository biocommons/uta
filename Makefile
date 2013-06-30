# UTA -- Universal Transcript Archive Makefile
# https://bitbucket.org/invitae/uta

.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail
SELF:=$(firstword $(MAKEFILE_LIST))
export PYTHONPATH=lib/python

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
#= INSTALLATION/SETUP HELP
setup: setup-python setup-perl

#=> setup-python: create a virtualenv (or provide your own)
# NOTE: setup-python only makes the virtualenv. You must actvate it
# yourself (source ve/bin/activate)
setup-python: virtualenv.py
	python $< --distribute ve
	source ve/bin/activate; python setup.py develop
virtualenv.py:
	curl https://raw.github.com/pypa/virtualenv/master/virtualenv.py >$@

#=> setup-perl: install perl packages
# TODO: consider perl brew instead
setup-perl:
	./sbin/perl-module-install --install-base ve   Log::Log4perl


############################################################################
#= 

develop:
	python setup.py develop

test:
	PYTHONPATH=lib/python python setup.py nosetests -v --with-xunit

docs:
	make -C doc html

package:
	python setup.py sdist upload


############################################################################
#= CLEANUP
.PHONY: clean cleaner cleanest pristine
#=> clean: clean up editor backups, etc.
clean:
	find . -name \*~ -print0 | xargs -0r /bin/rm
#=> cleaner: above, and remove generated files
cleaner: clean
	find . -name \*.pyc -print0 | xargs -0r /bin/rm -f
	/bin/rm -fr distribute-* *.egg *.egg-info
	make -C doc clean
#=> cleanest: above, and remove the virtualenv, .orig, and .bak files
cleanest: cleaner
	find . \( -name \*.orig -o -name \*.bak \) -print0 | xargs -0r /bin/rm -v
	/bin/rm -fr ve
#=> pristine: above, and delete anything unknown to mercurial
pristine: cleanest
	hg st -un0 | xargs -0r echo /bin/rm -fv
