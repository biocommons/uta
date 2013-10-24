#!/usr/bin/env python

import uta
from flask import Flask, jsonify, render_template, request
from flask.ext import restful
from flask.ext.restful import reqparse, Api, Resource
from uta.db.transcriptdb import TranscriptDB
from uta.tools.hgvsmapper import HGVSMapper

"""
Launch the webservice: gunicorn -w 4 -b 0.0.0.0:4000 uta_webservice:app

Example usage and output:

curl http://127.0.0.1:5000/uta/api/v1/hgvs_to_hgvsc -d "hgvsg=NC_000007.13:g.36561662C>T&ac=NM_001177507.1&ref=GRCh37.p10"
{
  "hgvsc": "NM_001177507.1:c.1486C>T",
  "hgvsp": "TBD",
  "uta_version": "version is not working..."
}
"""

"""
This example from the documentation shows that the status code is returned - this does not seem to be working. Instead
it only shows the message.
via: http://flask-restful.readthedocs.org/en/latest/quickstart.html
$ curl -d 'rate=foo' http://127.0.0.1:5000/
{'status': 400, 'message': 'foo cannot be converted to int'}
"""

app = Flask(__name__)
api = restful.Api(app)

#parser = reqparse.RequestParser()
hgvsmapper = HGVSMapper(db=TranscriptDB(), cache_transcripts=True)

# API URLs
HGVS_TO_HGVSC_URL = '/uta/api/v1/hgvs_to_hgvsc'
HGVS_TO_GENOMIC_COORDS_URL = '/uta/api/v1/hgvs_to_genomic_coords'

# RESTful interface using POST
# POST is necessary to properly encode the transcript names
class HGVSMapper_hgvs_to_hgvsc(restful.Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('hgvsg', type=str, help='Missing HGVS location e.g. hgvsg=NC_000007.13:g.36561662C>T',
                                 required=True)
        self.parser.add_argument('ac', type=str, help='Missing accession e.g. ac=NM_001177507.1',
                                 required=True)
        self.parser.add_argument('ref', type=str, help='Missing genomic build reference e.g. ref=GRCh37.p10',
                                 required=True)
        super(HGVSMapper_hgvs_to_hgvsc, self).__init__()

    def post(self):

        args = self.parser.parse_args()

        try:
            hgvsc = hgvsmapper.hgvsg_to_hgvsc(args['hgvsg'], ac=args['ac'], ref=args['ref'])
        except Exception as error:
            return jsonify({'message': 'Bad Request to HGVSMapper. {0}'.format(error)})

        uta_version = uta.__version__
        if uta_version is None:
            uta_version = 'version is not working...'

        return jsonify({'uta_version': uta_version,
                        'hgvsc': hgvsc,
                        'hgvsp': 'TBD'})


class HGVSMapper_hgvs_to_genomic_coords(restful.Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('hgvs', type=str, help='Missing HGVS location e.g. hgvs=NM_001177507.1:c.1486G>A',
                                 required=True)
        super(HGVSMapper_hgvs_to_genomic_coords, self).__init__()

    def post(self):
        args = self.parser.parse_args()

        try:
            chrom, chr_start, chr_end, tm = hgvsmapper.hgvs_to_genomic_coords(args['hgvs'])
        except Exception as error:
            return jsonify({'message': 'Bad Request to HGVSMapper. {0}'.format(error)})

        strand = None
        if tm is not None:
            strand = tm.strand_pm

        uta_version = uta.__version__
        if uta_version is None:
            uta_version = 'version is not working...'

        return jsonify({'chrom': chrom,
                        'chr_start': chr_start,
                        'chr_end': chr_end,
                        'strand': strand,
                        'uta_version': uta_version})


api.add_resource(HGVSMapper_hgvs_to_hgvsc, HGVS_TO_HGVSC_URL)
api.add_resource(HGVSMapper_hgvs_to_genomic_coords, HGVS_TO_GENOMIC_COORDS_URL)

@app.route('/')
def index():
    urls = {'hgvs_to_hgvsc': HGVS_TO_HGVSC_URL,
            'hgvs_to_genomic_coords': HGVS_TO_GENOMIC_COORDS_URL}

    base_url = request.base_url[:-1]    # remove the trailing '/'

    return render_template('index.html', base_url=base_url, urls=urls)


if __name__ == '__main__':
    app.run(debug=True)

