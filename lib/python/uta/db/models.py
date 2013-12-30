import collections

class Transcript(collections.namedtuple('Transcripts',[
            'ac', 'strand', 'cds_start_i', 'cds_end_i', 'gene', 'exons'
            ])):
    def __repr__(self):
        return '%s(%s; %d exons)' % (self.__class__, self.ac, len(self.exons))


class Exon(collections.namedtuple('Exon',[
            'start_i', 'end_i', 'name'
            ])):
    def __repr__(self):
        return '%s(%s,%s)' % (self.__class__,self.start_i,self.end_i)

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
