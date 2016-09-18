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
API Errors Jsonified
"""
import logging
from flask import Flask, jsonify, request, g, make_response
from apisrv import app, auth

logger = logging.getLogger(__name__)

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
    print("Bad Request")
    message = {
            'status': 400,
            'message': 'Bad Request: ' + request.url,
    }
    resp = jsonify(message)    
    resp.status_code = 400
    return resp


