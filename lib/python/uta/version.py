"""
populate __version__ and hg_id

Two cases:
1) _release.py exists: we get __hg_id__ from that file.
   _release.py is created during packaging, but is NOT added in hg.
   Therefore, this case applies mostly to deployed code.
2) Otherwise, fetch info by running 'hg id'.  This case applies
   mostly to development code.

Either way, __hg_id__ is a string like
17c1924c3d44+ default tip
or
17c1924c3d44 default 1.2.3

"""

from uta.utils.hgid import HgId

try:
    
    hg_id = HgId.init_from_hg(__file__)

except ImportError:

    from _release import hg_id
    hg_id = HgId.init_from_string( hg_id )

# __version__ will end up as a string like
# 'tip (33cdf1ff34a8+ default tip)'
# Then the repo is tagged as 1.2.3, the result
# will comply with http://semver.org/ recommendations
__version__ = hg_id.tag0
