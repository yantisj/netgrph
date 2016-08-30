#!/usr/bin/env python
#
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
"""
API User Functions
"""
import logging
import sys
from passlib.hash import sha256_crypt
import nglib

logger = logging.getLogger(__name__)

def add_user(username, passwd):
    """
    Add a new user to the database
    """

    ucheck = nglib.bolt_ses.run(
        'MATCH (u:User {username:{username}}) RETURN count(u)',
        {"username": username})

    if next(iter(ucheck))["count(u)"]:
        print("Error: User already exists in DB", file=sys.stderr)
        exit(1)
    else:
        logger.info("Adding new user to the database: %s", username)

        phash = sha256_crypt.encrypt(passwd)

        nglib.bolt_ses.run(
            'CREATE (u:User {username:{username}, phash:{phash}})',
            {"username": username, "phash": phash})

        return phash

def update_password(username, passwd):
    """ Update password for user """

    ucheck = nglib.bolt_ses.run(
        'MATCH (u:User {username:{username}}) RETURN count(u)',
        {"username": username})

    if next(iter(ucheck))["count(u)"]:
        logger.info("Updating password for user: %s", username)

        phash = sha256_crypt.encrypt(passwd)

        nglib.bolt_ses.run(
            'MATCH (u:User {username:{username}}) '
            + 'SET u.phash = {phash}', 
            {"username": username, "phash": phash})

        return phash
    else:

        print("Error: User does not exists in DB", file=sys.stderr)
        exit(1)

def authenticate_user(username, passwd):
    """ Authenticate a user """

    ucheck = nglib.bolt_ses.run(
        'MATCH (u:User {username:{username}}) RETURN u.phash as phash',
        {"username": username})

    authenticated = False

    for record in ucheck:
        authenticated = sha256_crypt.verify(passwd, record['phash'])
        break
    else:
        print("Error: User not found in DB", username, file=sys.stderr)
        return False
    
    if authenticated:
        logger.info("Successfully Authenticated user: %s", username)
    else:
        logger.info("Authentication Failed: %s", username)

    return authenticated

def del_user(username):
    """ Delete a user from the database """

    ucheck = nglib.bolt_ses.run(
        'MATCH (u:User {username:{username}}) RETURN count(u)',
        {"username": username})

    if next(iter(ucheck))["count(u)"]:
        nglib.bolt_ses.run(
            'MATCH (u:User {username:{username}}) DELETE u',
            {"username": username})
        return True
    else:
        return False
