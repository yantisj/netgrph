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
NetGrph API Server
"""
import os
import re
import json
from flask import Flask, jsonify, request
import nglib
import nglib.query
app = Flask(__name__)


# Default Config File Location
config_file = '/etc/netgrph.ini'
alt_config = './docs/netgrph.ini'

# Test/Dev Config
dirname = os.path.dirname(os.path.realpath(__file__))
if re.search(r'\/dev$', dirname):
    config_file = 'netgrphdev.ini'
elif re.search(r'\/test$', dirname):
    config_file = "netgrphdev.ini"


# Initialize Library
nglib.init_nglib(config_file)

@app.route('/')
def hello_world():
    ngtree = nglib.query.path.get_full_path('128.23.1.1', '128.23.200.186', {})
    ngjson = json.dumps(ngtree, indent=2, sort_keys=True)

    ngjson = ngjson.replace('\n', '<br>')

    dump = "<code>" + ngjson + "</code>"
    return dump

@app.route('/netgrph/api/v1.0/path', methods=['GET'])
def get_full_path():
    print(request.args)
    return jsonify(nglib.query.path.get_full_path(request.args['src'], \
        request.args['dst'], {}))
