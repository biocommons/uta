def get_hg_id(root):
    "return a string with mercurial id data (hg id)"
    import subprocess
    try:
        return subprocess.check_output([
            'hg', '-R', root, 'id', '-bit', 
            '--config', 'trusted.users=*',    # prevents "Not trusting file..." warning
            ]).rstrip()
    except:
        return None

def get_hg_id_dict(root):
    "return a dict of hg changeset, branch, and tag"
    return dict( zip( 
            ['root','changeset','branch','tag'],
            [root] + version.split()
            ) )

def find_hg_root(path):

def find_hg_root(path):
    "return hg root for a given file/dir path (e.g., package.__file__)"
    root = os.path.abspath(path)
    while root:
        if os.path.exists( os.path.join( root, '.hg' ) ):
            return root
        root = os.path.dirname(root)
    return None


