#!/bin/sh
# Change to the current netgrph folder
export NGHOME=/home/netgrph/netgrph
export NGCSV=/home/netgrph/csv
export NETDBDATA=/opt/netdb/data

cd $NGHOME/datasources/
./netdb-nd.py -nf $NETDBDATA/nd.csv -of $NGCSV/nd.csv
./netdb-devfile.py -df $NETDBDATA/devicelist.csv -of $NGCSV/devices.csv
