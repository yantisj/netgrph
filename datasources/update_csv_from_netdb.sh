#!/bin/sh
# Change to the current folder, wherever that is
cd /home/yantisj/netgrph/dev/datasources/
./netdb-nd.py -nf /opt/netdb/data/nd.csv -of /home/yantisj/csv/nd.csv
./netdb-devfile.py -df /scripts/devicelist.csv -of /home/yantisj/csv/devices.csv
