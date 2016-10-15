#!/usr/bin/env python
# Copyright (c) 2016 "Jonathan Yantis"
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
"""
API Views for serving user requests with examples
Add your own methods here
"""
import logging
import nglib
import nglib.query
from nglib.exceptions import ResultError
from flask import jsonify, request
from apisrv import app, auth, config, errors

# Setup
logger = logging.getLogger(__name__)
app_name = config['apisrv']['app_name']

@app.route('/netgrph/api/v1.0/path', methods=['GET'])
@auth.login_required
def get_full_path():
    onepath = False
    if 'onepath' in request.args:
        if request.args['onepath'] == "True":
            onepath = True
    try:
        return jsonify(nglib.query.path.get_full_path(request.args['src'], \
            request.args['dst'], {"onepath": onepath}))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/rpath', methods=['GET'])
@auth.login_required
def get_routed_path():
    """ Routed Path """
    onepath = False
    if 'onepath' in request.args:
        if request.args['onepath'] == "True":
            onepath = True
    try:
        return jsonify(nglib.query.path.get_routed_path(request.args['src'], \
            request.args['dst'], {"onepath": onepath, "depth": request.args['depth'], \
            "VRF": request.args['vrf']}))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/spath', methods=['GET'])
@auth.login_required
def get_switched_path():
    """ Switched Path """
    onepath = False
    if 'onepath' in request.args:
        if request.args['onepath'] == "True":
            onepath = True
    try:
        return jsonify(nglib.query.path.get_switched_path(request.args['src'], \
            request.args['dst'], {"onepath": onepath, "depth": request.args['depth']}))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/net', methods=['GET'])
@auth.login_required
def get_net():

    try:
        return jsonify(nglib.query.net.get_networks_on_cidr(request.args['cidr'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/ip', methods=['GET'])
@auth.login_required
def get_ip():

    try:
        return jsonify(nglib.query.net.get_net(request.args['ip'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/nlist', methods=['GET'])
@auth.login_required
def get_nlist():

    try:
        return jsonify(nglib.query.net.get_networks_on_filter(request.args['group'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/nfilter', methods=['GET'])
@auth.login_required
def get_nfilter():
    """ Networks on a filter """
    try:
        return jsonify(nglib.query.net.get_networks_on_filter(nFilter=request.args['filter'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/vid', methods=['GET'])
@auth.login_required
def get_vid():
    allSwitches = True
    if 'allSwitches' in request.args and request.args['allSwitches'] == 'False':
        allSwitches = False
    try:
        return jsonify(nglib.query.vlan.search_vlan_id(request.args['id'], \
                    rtype="NGTREE", allSwitches=allSwitches))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))


@app.route('/netgrph/api/v1.0/vtree', methods=['GET'])
@auth.login_required
def get_vtree():
    try:
        return jsonify(nglib.query.vlan.get_vtree(request.args['name'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/dev', methods=['GET'])
@auth.login_required
def get_dev():
    try:
        return jsonify(nglib.query.dev.get_device(request.args['dev'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

# Info method, Return Request Data back to client as JSON
@app.route('/' + app_name + '/api/v1.0/info', methods=['POST', 'GET'])
@auth.login_required
def app_getinfo():
    """ Returns Flask API Info """
    response = dict()
    response['message'] = "Flask API Data"
    response['status'] = "200"
    response['method'] = request.method
    response['path'] = request.path
    response['remote_addr'] = request.remote_addr
    response['user_agent'] = request.headers.get('User-Agent')

    # GET attributes
    for key in request.args:
        response['GET ' + key] = request.args.get(key, '')
    # POST Attributes
    for key in request.form.keys():
        response['POST ' + key] = request.form[key]

    return jsonify(response)

@app.route('/')
def app_index():
    """Index identifying the server"""
    response = {"message": app_name + \
                " server: Authentication required for use",
                "status": "200"}
    return jsonify(response)
