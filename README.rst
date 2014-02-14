===================================
UTA -- Universal Transcript Archive
===================================

*bringing smiles to transcript users since 2013*

`Docs <http://pythonhosted.org/uta/>`_ | `PyPI <https://pypi.python.org/pypi/uta>`_ | |build_status|


Overview
--------

The UTA stores transcripts aligned to genome reference assemblies using
multiple methods in order to improve the precision and accuracy by which
the scientific and clinical communities describe variants.

It will facilitate the following:

* enabling an interpretation of variants reported in literature against
  obsolete transcript records
* identifying regions where transcript and reference genome sequence
  assemblies disagree
* characterizing transcripts of the same gene across transcript sources
* identifying transcripts and genomic regions with ambiguous alignments
  that may affect clinical interpretation
* querying for multiple transcript sources through a single
  interface

UTA is used by the `hgvs`_ package to map variants between genomic,
transcript, and protein coordinates.


Installation
------------

Tested on Ubuntu 13.04, Python 2.7.5::

  $ pip install hg+ssh://hg@bitbucket.org/invitae/uta

Alternatively, you may clone and install::

  $ pip clone hg+ssh://hg@bitbucket.org/invitae/uta
  $ cd uta
  $ make install
  (or, equivalently, python setup.py install)


Development and Testing
-----------------------

To develop UTA, follow these steps.

1. Setup a virtual environment.

  With virtualenvwrapper_::

    mkvirtualenv uta-ve

  Or, with virtualenv_::

    cd ~
    virtualenv uta-ve
    source uta-ve/bin/activate

2. Clone UTA.::

    hg clone ssh://hg@bitbucket.org/invitae/uta
    cd uta
    make develop

3. Restore a database or load a new one

  UTA currently expects to have an existing database available. When the
  loaders are available, instructions will appear here.  For now, creating
  an instance of TranscriptDB without arguments will cause it to connect
  to a populated Invitae database.


.. _hgvs: https://bitbucket.org/invitae/hgvs
.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _virtualenvwrapper: http://virtualenvwrapper.readthedocs.org/en/latest/install.html


.. |build_status| image:: https://drone.io/bitbucket.org/invitae/uta/status.png
  :target: https://drone.io/bitbucket.org/invitae/uta
  :align: middle
