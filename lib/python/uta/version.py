"""
populate __version__ and __hg_id__

Two cases:
1) _release.py exists: we get __hg_id__ from that file.
   _release.py is created during packaging, but is NOT added in hg.
   Therefore, this case applies mostly to deployed code.
2) Otherwise, fetch info by running 'hg id'.  This case applies
   mostly to development code.

Either way, __hg_id__ is a string like
17c1924c3d44+ default tip
or
17c1924c3d44 default rel-1.2.3

If the tag contains rel-, the following text is used for __version__.
Otherwise, __version__ is 'dev'

http://semver.org/
"""

try:

    from _release import __hg_id__

except ImportError:

    import os,subprocess

    def find_hg_root(path):
        "return hg root for a given file/dir path (e.g., package.__file__)"
        root = os.path.abspath(path)
        while root:
            if os.path.exists( os.path.join( root, '.hg' ) ):
                return root
            root = os.path.dirname(root)
        return None

    def fetch_hg_id():
        return subprocess.check_output([
            'hg', '-R', find_hg_root(__file__), 'id', '-bit', 
            '--config', 'trusted.users=*',    # prevents Not trusting file...
            ]).rstrip()
    
    __hg_id__ = fetch_hg_id() or 'hg id not available'


hg_info = dict(zip(['changeset','branch','tag'],__hg_id__.split()))

__version__ = 'dev'
if hg_info['tag'].startswith('rel-'):
    __version__ = hg_info['tag'].replace('rel-','')
