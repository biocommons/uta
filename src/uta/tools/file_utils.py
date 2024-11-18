import gzip
from contextlib import contextmanager


@contextmanager
def open_file(filename):
    if filename.endswith(".gz"):
        with gzip.open(filename, "rt") as f:
            yield f
    else:
        with open(filename) as f:
            yield f
