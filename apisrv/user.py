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
API User Functions
"""
import sys
import logging
import time
from passlib.hash import sha256_crypt

import sqlite3
from flask_sqlalchemy import SQLAlchemy
from apisrv import auth, config, db
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

class User(db.Model):
    """ SQL User Model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120), unique=True)
    role = db.Column(db.String(40))

    def __init__(self, username, password, role='default'):
        self.username = username
        self.password = password
        self.role = role

    def __repr__(self):
        return '<User {:}>'.format(self.username)

@auth.verify_password
def verify_password(username, password):
    """API Password Verification"""

    if authenticate_user(username, password):
        return True
    return False

def authenticate_user(username, passwd):
    """ Authenticate a user """

    try:
        user = User.query.filter_by(username=username).first()
    except OperationalError:
        db.create_all()
        user = User.query.filter_by(username=username).first()


    authenticated = False

    if user:
        authenticated = sha256_crypt.verify(passwd, user.password)
    else:
        time.sleep(1)
        logger.info("Authentication Error: User not found in DB: %s", username)
        return False
    
    if authenticated:
        logger.debug("Successfully Authenticated user: %s", username)
    else:
        logger.info("Authentication Failed: %s", username)

    return authenticated


def add_user(username, passwd):
    """
    Add a new user to the database
    """

    user = User.query.filter_by(username=username).first()

    if user:
        #print("Error: User already exists in DB", file=sys.stderr)
        raise Exception("Error: User already exists in DB")
    elif len(passwd) < 6:
        print("Error: Password must be 6 or more characters", file=sys.stderr)
        exit(1)       
    else:
        logger.info("Adding new user to the database: %s", username)

        phash = sha256_crypt.encrypt(passwd)
        
        newuser = User(username, phash)
        db.session.add(newuser)
        db.session.commit()

        return phash

def update_password(username, passwd):
    """ Update password for user """

    user = User.query.filter_by(username=username).first()

    if len(passwd) < 6:
        print("Error: Password must be 6 or more characters", file=sys.stderr)
        exit(1)
    elif user:
        logger.info("Updating password for user: %s", username)

        phash = sha256_crypt.encrypt(passwd)

        user.password = phash
        db.session.commit()

        return phash
    else:

        print("Error: User does not exists in DB", file=sys.stderr)
        exit(1)

def del_user(username):
    """ Delete a user from the database """

    user = User.query.filter_by(username=username).first()

    if user:
        logger.info("Deleting user: %s", username)

        db.session.delete(user)
        db.session.commit()

        return True
    else:

        print("Error: User does not exists in DB", file=sys.stderr)
        exit(1)

