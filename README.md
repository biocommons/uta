# uta -- Universal Transcript Archive

*bringing smiles to transcript users since 2013*

[![docker_badge](https://img.shields.io/docker/pulls/biocommons/uta.svg?maxAge=2592000)](https://hub.docker.com/r/biocommons/uta/)

The UTA (Universal Transcript Archive) stores transcripts aligned to
sequence references (typically genome reference assemblies). It supports
aligning the same transcript to multiple references using multiple
alignment methods. Specifically, it facilitates the following:

-   Querying for multiple transcript sources through a single interface
-   Interpretating variants reported in literature against obsolete
    transcript records
-   Identifying regions where transcript and reference genome sequence
    assemblies disagree
-   Comparing transcripts across from distinct sources
-   Comparing transcript alignments generated by multiple methods
-   Identifying ambiguities in transcript alignments

UTA is used by the [hgvs](https://github.com/biocommons/hgvs) package to
map variants between genomic, transcript, and protein coordinates.

This code repository is primarily used for *generating* the UTA
database. The primary interface for the database itself is via direct
PostgreSQL access. (A [REST interface](https://github.com/biocommons/uta/issue/164/) is planned, but not yet available.)

Users can access a public instance of UTA or build their own instance of
the database.

## Accessing the Public UTA Instance

Invitae provides a public instance of UTA. The connection parameters
are:

**param**    | **value**
------------ | --------------------
**host**     | `uta.biocommons.org`
**port**     | `5432` (default)
**database** | `uta`
**login**    | `anonymous`
**password** | `anonymous`

For example:

    $ PGPASSWORD=anonymous psql -h uta.biocommons.org -U anonymous -d uta

Or, in Python (requires [psycopg2](https://pypi.org/project/psycopg2/)):

    > import psycopg2, psycopg2.extras
    > conn = psycopg2.connect("host=uta.biocommons.org dbname=uta user=anonymous password=anonymous")
    > cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    > cur.execute("select * from uta_20140210.tx_def_summary_v where hgnc='BRCA1'")
    > row = cur.fetchone()
    > dict(row)
    {'hgnc': 'BRCA1',
    'cds_md5': 'b3d16af258a759d0321d4f83b55dd51b',
    'es_fingerprint': 'f91ab768a35c8db477fbf04dde6955e2',
    'tx_ac': 'ENST00000357654',
    'alt_ac': 'ENST00000357654',
    'alt_aln_method': 'transcript',
    'alt_strand': 1,
    'exon_set_id': 7027,
    'n_exons': 23,
    'se_i': '0,100;100,199;199,253;253,331;331,420;420,560;560,666;666,712;712,789;789,4215;4215,4304;4304,4476;4476,4603;4603,4794;4794,5105;5105,5193;5193,5271;5271,5312;5312,5396;5396,5451;5451,5525;5525,5586;5586,7094',
    'starts_i': [0,
    100,
    199,
    253,
    331,
    420,
    560,
    666,
    712,
    789,
    4215,
    4304,
    4476,
    4603,
    4794,
    5105,
    5193,
    5271,
    5312,
    5396,
    5451,
    5525,
    5586],
    'ends_i': [100,
    199,
    253,
    331,
    420,
    560,
    666,
    712,
    789,
    4215,
    4304,
    4476,
    4603,
    4794,
    5105,
    5193,
    5271,
    5312,
    5396,
    5451,
    5525,
    5586,
    7094],
    'lengths': [100,
    99,
    54,
    78,
    89,
    140,
    106,
    46,
    77,
    3426,
    89,
    172,
    127,
    191,
    311,
    88,
    78,
    41,
    84,
    55,
    74,
    61,
    1508],
    'cds_start_i': 119,
    'cds_end_i': 5711}

## Installing UTA Locally

### Installing with Docker (preferred)

[Docker](http://docker.com) enables the distribution of lightweight,
isolated packages that run on essentially any platform. When you use
this approach, you will end up with a local UTA installation that runs
as a local PostgreSQL process. The only requirement is Docker itself -
you will not need to install PostgreSQL or any of its dependencies.

1.  [Install Docker](https://docs.docker.com/installation/).

2.  Define the UTA version to download. A list of available versions
    can be found [here](https://hub.docker.com/r/biocommons/uta/tags):

        $ uta_v=uta_20210129b

    This variable is used only for consistency in the examples that
    follow. Defining this variable is not required for any other reason.

    The UTA version string indicates the data release date. The tag is
    made at the time of loading and is used to derive the filename for
    the database dumps and docker images. Therefore, the public
    c instances, database dumps, and docker images will always
    contain exactly the same content.

3.  Fetch the UTA Docker image from Docker Hub:

        $ docker pull biocommons/uta:$uta_v

    This process will likely take 1-3 minutes.

4.  Run the image:

        $ docker run \
           -d \
           -e POSTGRES_PASSWORD=some-password-that-you-make-up \
           -v /tmp:/tmp \
           -v uta_vol:/var/lib/postgresql/data \
           --name $uta_v \
           --network=host \
           biocommons/uta:$uta_v

    The first time you run this image, it will initialize a PostgreSQL
    database cluster, then download a database dump from biocommons and install it.

    `-d` starts the container in daemon (background) mode. To see
    progress:

        $ docker logs -f $uta_v

    You will see messages from several processes running in parallel.
    Near the end, you'll see:

        == You may now connect to uta.  No password is required.
        ...
        2020-05-28 22:08:45.654 UTC [1] LOG:  database system is ready to accept connections

    Hit Ctrl-C to stop watching logs. The container will still be
    running.

5.  Test your installation

    With the test commands below, you should see a table dump with at
    least 4 lines showing schema_version, create date, license, and uta
    (code) version used to build the instance.

        $ psql -h localhost -U anonymous -d uta -c "select * from $uta_v.meta"
        
              key       |                               value                                
        ----------------+--------------------------------------------------------------------
         schema_version | 1.1
         created on     | 2015-08-21T10:53:50.666152
         license        | CC-BY-SA (http://creativecommons.org/licenses/by-sa/4.0/deed.en_US
         uta version    | 0.2.0a2.dev11+n52ed6e969cfc
         (4 rows)

6.  (Optional) To configure [hgvs](https://github.com/biocommons/hgvs)
    to use this local installation, consult the 
    [hgvs documentation](https://hgvs.readthedocs.io/en/latest/installation.html#local-installation-of-uta-optional)

### Installing from database dumps

Users should prefer the public UTA instance (uta.biocommons.org) or the
Docker installation wherever possible. When those options are not
available, users may wish to create a local PostgreSQL database from
database dumps. Users choosing this method of installation should be
experienced with PostgreSQL administration.

The public site and Docker images are built from exactly the same dumps
as provided below. Building a database from these should result in a
local database that is essentially identical to those options.

Due to the heterogeneity of operating systems and PostgreSQL
installations, **installing from database dumps is unsupported**.

*The following commands will likely need modification appropriate for
the installation environment.*

1.  Download an appropriate database dump from
    [dl.biocommons.org](http://dl.biocommons.org/uta/).

2.  Create a user and database.

    You may choose any username and database name you like. uta and
    uta_admin are likely to ease installation.

        $ createuser -U postgres uta_admin
        $ createdb -U postgres -O uta_admin uta 

3.  Restore the database.

        $ gzip -cdq uta_20150827.pgd.gz | psql -U uta_admin -1 -v ON_ERROR_STOP=1 -d uta -Eae

## Developer Setup

To develop UTA, follow these steps.

1.  Set up a virtual environment using your preferred method.
    For example:

        $ python3 -m venv uta-venv
        $ source uta-venv/bin/activate

2.  Clone UTA and install:

        $ git clone git@github.com:biocommons/uta.git
        $ cd uta
        $ pip install -e .[test]

3.  Restore a database or load a new one using the instructions [above](#installing-from-database-dumps).

4.  To run the tests:

        $ python3 -m unittest
