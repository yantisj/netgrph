#!/bin/sh
#
# Sets password to "your_passwd" for automated testing
#
curl -H "Content-Type: application/json" -X POST -d '{"password":"your_passwd"}' -u neo4j:neo4j http://localhost:7474/user/neo4j/password
