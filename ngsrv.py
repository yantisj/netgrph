#!/usr/bin/env python3
#
# Copyright (c) 2016 "Jonathan Yantis"
#
# This file is a part of NetGrph.
#
#    This program is free software: you can redistribute it and/or  modify
#    it under the terms of the GNU Affero General Public License, version 3,
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    As a special exception, the copyright holders give permission to link the
#    code of portions of this program with the OpenSSL library under certain
#    conditions as described in each individual source file and distribute
#    linked combinations including the program with the OpenSSL library. You
#    must comply with the GNU Affero General Public License in all respects
#    for all of the code used other than as permitted herein. If you modify
#    file(s) with this exception, you may extend this exception to your
#    version of the file(s), but you are not obligated to do so. If you do not
#    wish to do so, delete this exception statement from your version. If you
#    delete this exception statement from all source files in the program,
#    then also delete it in the license file.
#
#
"""
NetGrph API Server (work in progress)
"""
import os
import re
import logging
from flask import Flask, jsonify, request, g, make_response
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException
import nglib
import nglib.query
import nglib.api.user

app = Flask(__name__)
logger = logging.getLogger(__name__)
auth = HTTPBasicAuth()

limiter = Limiter(
    app,
    key_func=get_remote_address,
    global_limits=["1000 per day", "100 per hour", "5 per minute"]
)

verbose = 1

# Default Config File Location
config_file = '/etc/netgrph.ini'
alt_config = './docs/netgrph.ini'

# Test/Dev Config
dirname = os.path.dirname(os.path.realpath(__file__))
if re.search(r'\/dev$', dirname):
    config_file = 'netgrphdev.ini'
elif re.search(r'\/test$', dirname):
    config_file = "netgrphdev.ini"


@app.route('/test')
@auth.login_required
def app_test():

    return jsonify(nglib.query.net.get_net('128.23.1.1', \
        rtype="NGTREE", verbose=False))

@app.route('/netgrph/api/v1.0/path', methods=['GET'])
@auth.login_required
def get_full_path():
    onepath = False
    if 'onepath' in request.args:
        if request.args['onepath'] == "True":
            onepath = True
    return jsonify(nglib.query.path.get_full_path(request.args['src'], \
        request.args['dst'], {"onepath": onepath}))


@app.route('/netgrph/api/v1.0/net', methods=['GET'])
@auth.login_required
def get_net():

    return jsonify(nglib.query.net.get_net(request.args['ip'], rtype="NGTREE"))

@app.route('/netgrph/api/v1.0/nlist', methods=['GET'])
@auth.login_required
def get_nlist():

    return jsonify(nglib.query.net.get_networks_on_filter(request.args['group'], rtype="NGTREE"))

@app.errorhandler(404)
def not_found(error=None):
    message = {
            'status': 404,
            'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

@app.errorhandler(429)
def ratelimit_handler(e):
    return make_response(
            jsonify(error="ratelimit exceeded %s" % e.description)
            , 429
    )

@auth.error_handler
def auth_failed(error=None):
    message = {
            'status': 401,
            'message': 'Authentication Failed: ' + request.url
    }
    resp = jsonify(message)
    resp.status_code = 401

    return resp

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'nglib'):
        logger.info("Closing Database Connection")

@auth.verify_password
def verify_password(username, password):

    # Initialize Library On Authentication

    nglib.verbose = verbose
    nglib.init_nglib(config_file)

    if not nglib.api.user.authenticate_user(username, password):
        return False
    g.user = username
    return True


if __name__ == "__main__":
    context = ('/Users/yantisj/netgrph/newhal.crt', '/Users/yantisj/netgrph/newhal.key')

    app.run(host='0.0.0.0', port=5000, ssl_context=context, threaded=True, debug=True)
