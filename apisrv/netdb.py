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
NetDB API Views
"""
import logging
import nglib
import nglib.query
import nglib.report
import nglib.netdb.switch
from nglib.exceptions import ResultError
from flask import jsonify, request
from apisrv import app, auth, config, errors

# Setup
logger = logging.getLogger(__name__)
app_name = config['apisrv']['app_name']

# Device Queries
@app.route('/netdb/api/v1.0/table/arp', methods=['GET'])
@auth.login_required
def get_arptable():
    """ Get ARP Tables from NetDB
    """
    router = None
    hours = 1

    if 'router' in request.args:
        router = request.args['router']
        router = router.replace('*', '%')
    else:
        return jsonify(errors.json_error('InputError', 'router= is required'))

    if 'hours' in request.args:
        hours = int(request.args['hours'])


    try:
        return jsonify(nglib.netdb.ip.arp(router=router, hours=hours))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netdb/api/v1.0/table/mac', methods=['GET'])
@auth.login_required
def get_mactable():
    """ Get the MAC Table from NetDB
    """
    switch = None
    port = '%'
    hours = 1

    if 'switch' in request.args:
        switch = request.args['switch']
        switch = switch.replace('*', '%')
    else:
        return jsonify(errors.json_error('InputError', 'switch= is required'))
    if 'port' in request.args:
        port = request.args['port']
        port = port.replace('*', '%')
        print("port", port)

    if 'hours' in request.args:
        hours = int(request.args['hours'])

    try:
        return jsonify(nglib.netdb.switch.mac(switch=switch, port=port, hours=hours))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netdb/api/v1.0/table/mac/<switch>/count', methods=['GET'])
@auth.login_required
def get_mac_count(switch):
    """ Get the MAC Table count from NetDB
    """
    hours = 1
    switch = switch.replace('*', '%')

    if 'hours' in request.args:
        hours = int(request.args['hours'])

    try:
        return jsonify(nglib.netdb.switch.count(switch=switch, hours=hours))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))
