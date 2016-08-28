#!/bin/sh
./ngupdate.py -v --dropDatabase
sleep 2
./ngupdate.py -ivrf -v
./ngupdate.py -id -v
./ngupdate.py -ind -v
./ngupdate.py -v -inet --ignoreNew
./ngupdate.py -isnet -v
./ngupdate.py -ivlan -v --ignoreNew
./ngupdate.py -uvlan -v
./ngupdate.py -ifw -v
./ngupdate.py -v -ifile ./cypher/buildfw.cyp
./ngupdate.py -v -ifile ./cypher/constraints.cyp
./ngupdate.py -full -v
./ngupdate.py -v -ifile ./cypher/buildfw.cyp
./test/test_full.sh
