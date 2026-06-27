# Developer Setup

This guide covers setting up a local environment for developing UTA itself. If
you only want to *use* UTA, see [Installing UTA Locally](../README.md#installing-uta-locally)
in the main README instead.

## Virtual Environment
To develop UTA, follow these steps.

1.  Set up a virtual environment using your preferred method.
    For example:

        $ python3 -m venv uta-venv
        $ source uta-venv/bin/activate

2.  Clone UTA and install:

        $ git clone git@github.com:biocommons/uta.git
        $ cd uta
        $ pip install -e .[test]

3.  Restore a database or load a new one using the instructions in
    [Installing from database dumps](../README.md#installing-from-database-dumps).

4.  To run the tests:

        $ python3 -m unittest

## Docker

1. Clone UTA and build docker image:

        $ git clone git@github.com:biocommons/uta.git
        $ cd uta
        $ docker build -t uta .

2. Restore a database or load a new one using the instructions in
   [Installing from database dumps](../README.md#installing-from-database-dumps).

3. Run container and tests

        $ docker run -it --rm uta bash

4. Testing

        $ docker build --target uta-test -t uta-test .
        $ docker run --rm uta-test python -m unittest
