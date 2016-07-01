#!/bin/sh
pylint3 ./nglib/ netgrph.py ngupdate.py > ./log/pylint.log
less ./log/pylint.log
