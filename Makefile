.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE
.DELETE_ON_ERROR:

SHELL:=/bin/bash -o pipefail

-include .uta.conf.mk
.uta.conf.mk: etc/uta.conf
	./sbin/conf-to-vars $< >$@

setup: setup-python setup-perl

setup-python: virtualenv.py
	python $< --distribute ve
	source ve/bin/activate; python setup.py develop
virtualenv.py:
	curl https://raw.github.com/pypa/virtualenv/master/virtualenv.py >$@

# TODO: consider perl brew instead
setup-perl:
	./sbin/perl-module-install --install-base ve   Log::Log4perl

develop:
	python setup.py develop

test:
	PYTHONPATH=lib/python python setup.py nosetests -v --with-xunit


############################################################################
### CLEANUP
.PHONY: clean cleaner cleanest pristine
clean:
	find . -name \*~ -print0 | xargs -0r /bin/rm
cleaner: clean
	find . \( -name \*.orig -o -name \*.bak \) -print0 | xargs -0r /bin/rm -v
	find . -name \*.pyc -print0 | xargs -0r /bin/rm -f
	/bin/rm -fr distribute-* *.egg *.egg-info
cleanest: cleaner
	/bin/rm -fr ve
pristine: cleanest
	# deleting anything unknown to mercurial, including your
	# precious uncommitted changes
	hg st -un0 | xargs -0r echo /bin/rm -fv
