"""
populate __version__ and hg_id

Two cases:
1) Try to fetch SCM info by running 'hg id'.  This case applies
   mostly to development code.
2) If that fails, look for _release.py.
   _release.py is created during packaging, but is NOT added in hg.
   Therefore, this case applies mostly to deployed code that
   doesn't have a .hg directory somewhere along the path to __file__.
"""

from uta.utils.hgid import HgId

try:
    
    hg_id = HgId.init_from_hg(__file__)
    __version__ = hg_id.version

except:

    try:

        from _release import hg_id
        hg_id = HgId.init_from_string( hg_id )
        __version__ = hg_id.version

    except ImportError:

        hg_id = None
        __version__ = None


## <LICENSE>
## Copyright 2014 UTA Contributors (https://bitbucket.org/invitae/uta)
## 
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
## 
##     http://www.apache.org/licenses/LICENSE-2.0
## 
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## </LICENSE>
