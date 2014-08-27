def human_to_ci(s,e=None):
    """convert start,end interval in inclusive, discontinuous HGVS coordinates
    (..,-2,-1,1,2,..) to continuous interbase (right-open) coordinates
    (..,-2,-1,0,1,..)"""
    def _cds_to_ci(c):
        assert c != 0, 'received CDS coordinate 0; expected ..,-2,-1,1,1,...'
        return c-1 if c>0 else c
    return _cds_to_ci(s), None if e is None else _cds_to_ci(e)+1

def ci_to_human(s,e=None):
    """convert start,end interval in continuous interbase (right-open)
    coordinates (..,-2,-1,0,1,..) to discontinuous HGVS coordinates
    (..,-2,-1,1,2,..)"""
    def _ci_to_cds(c):
        return c+1 if c>=0 else c
    return _ci_to_cds(s), None if e is None else _ci_to_cds(e)-1

cds_to_ci = human_to_ci
ci_to_cds = ci_to_human

## <LICENSE>
## Copyright 2014 UTA Contributors (https://bitbucket.org/uta/uta)
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
