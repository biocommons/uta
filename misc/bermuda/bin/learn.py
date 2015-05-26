#!/usr/bin/env python

from sklearn import tree
from sklearn.externals.six import StringIO
import pydot

# https://docs.google.com/a/invitae.com/spreadsheet/ccc?key=0ArCkc7BhL450dDRZTmE0djk3bHIxRVdMMlF0WTBoV3c&rm=full#gid=7
# class	sb_se_i_eq	sb_status_eq	s_refagree	b_refagree	s_trivial	b_trivial
data = """
S	C	A0	t	t	t	t	t	t
S	C	A2	f	f	t	f	t	f
S	C	A2	f	f	t	f	t	t
B	C	A6	f	f	f	t	f	t
B	C	A6	f	f	f	t	t	t
S	W	B0	t	t	f	f	t	t
S	W	C2	f	t	t	t	t	t
S	W	C4	f	f	f	f	t	f
S	W	C4	f	f	f	f	t	t
S	W	C4	f	t	f	f	t	f
S	W	C4	f	t	f	f	t	t
B	W	C6	f	f	f	f	f	t
x	x	D	t	t	f	f	f	f
x	x	F	f	t	f	f	f	f
x	x	F	f	f	f	f	f	f
""".strip()


def bool_str_to_float(s):
    if s == 't':
        return 1
    if s == 'f':
        return -1
    raise RuntimeError()


def write_pdf(clf, fn):
    dot_data = StringIO()
    tree.export_graphviz(clf, out_file=dot_data)
    graph = pydot.graph_from_dot_data(dot_data.getvalue())
    graph.write_pdf(fn)


fv = []
cv = []
av = []
wv = []
for row in data.splitlines():
    d = row.split()
    a, w, c, f = d[0], d[1], d[2], map(bool_str_to_float, d[3:])
    fv += [f]
    cv += [c]
    wv += [w]
    av += [a]


a_clf = tree.DecisionTreeClassifier()
a_clf.fit(fv, av)
write_pdf(a_clf, '/tmp/a.pdf')

c_clf = tree.DecisionTreeClassifier()
c_clf.fit(fv, cv)
write_pdf(c_clf, '/tmp/c.pdf')

w_clf = tree.DecisionTreeClassifier()
w_clf.fit(fv, wv)
write_pdf(w_clf, '/tmp/w.pdf')

import IPython
IPython.embed()
