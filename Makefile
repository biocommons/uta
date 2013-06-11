.SUFFIXES :
.PRECIOUS :
.PHONY : FORCE

SHELL:=/bin/bash -o pipefail

setup: install-perl-modules

install-perl-modules:
	./sbin/perl-module-install --install-base ve   Log::Log4perl



############################################################################
### CLEANUP
.PHONY: clean cleaner cleanest pristine
clean:
	find . -name \*~ -print0 | xargs -0r /bin/rm
cleaner: clean
	find . \( -name \*.orig -o -name \*.bak \) -print0 | xargs -0r /bin/rm -v
cleanest: cleaner
	/bin/rm -fr *.egg-info ve
pristine: cleanest
	# deleting anything unknown to mercurial, including your
	# precious uncommitted changes
	hg st -un0 | xargs -0r echo /bin/rm -fv
