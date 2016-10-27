#/bin/sh
export NGHOME=/home/netgrph/netgrph
export NGCSV=/home/netgrph/csv
export NETDBDATA=/opt/netdb/data

$NGHOME/datasources/ciscoparse.py -vr 1-4096 -ivr 0-4096 -df $NGCSV/devices.csv -dfile $NGCSV/devinfo.csv -mf /scripts/versions.txt -lfile $NGCSV/links.csv -ifile $NGCSV/allnets.csv -vfile $NGCSV/allvlans.csv
$NGHOME/datasources/asaparse.py -fd $NGCSV/asafirewalls.csv -debug 0 -ffile $NGCSV/firewalls.csv
