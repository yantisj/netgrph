#/bin/sh
/home/yantisj/netgrph/prod/datasources/ciscoparse.py -vr 2-4096 -ivr 0-4096 -df /home/yantisj/csv/devices.csv -dfile /home/yantisj/csv/devinfo.csv -ifile /home/yantisj/csv/allnets.csv -vfile /home/yantisj/csv/allvlans.csv
/home/yantisj/netgrph/dev/datasources/asaparse.py -fd ~/csv/asafirewalls.csv -debug 0 -ffile /home/yantisj/csv/firewalls.csv
