#!/bin/bash -e

test_dir=$(mktemp -d -t uta-XXXXX)
test_env=$(basename $test_dir)

mkvirtualenv $test_env

set -x

cd $test_dir
hg clone ssh://hg@bitbucket.org/uta/uta-align
cd uta-align
make install
cd ..

hg clone ssh://hg@bitbucket.org/uta/uta
cd uta
make develop
make develop
cd loading
make test-build

