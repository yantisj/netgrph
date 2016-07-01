## Install Notes

Netgrph was built on Ubuntu 14.04 LTS but should be portable to any other Python
3.4+ system. I have done limited testing at this point on other systems (MacOS),
so I highly recommend this OS right now. In the near future, I plan to ship a
set of ansible scripts for easy install, but at first this is what I have.

### Test Install Instructions

- For testing, you can install everything but the database under your user on any system
- If you do not have root access to your system, use virtualenv to satisfy the pip requirements

- Clone the github repository to ~/
- Install [Neo4j Community Edition](http://neo4j.com/download/) (available as a package for Ubuntu but requires java8+)
```
## Python system requirements includes testing libraries
sudo apt-get install python3-pip python3-pytest python3-logilab-common

# Java and Neo4j
sudo add-apt-repository ppa:webupd8team/java

sudo apt-get update
echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections
sudo apt-get install oracle-java8-installer
wget -O - https://debian.neo4j.org/neotechnology.gpg.key | sudo apt-key add -
echo 'deb http://debian.neo4j.org/repo stable/' >/tmp/neo4j.list
sudo mv /tmp/neo4j.list /etc/apt/sources.list.d
sudo apt-get update
sudo apt-get install neo4j
```

- To allow remote connections to neo4j, open this file and uncomment this line:
```
sudo vim /etc/neo4j/neo4j.conf
dbms.connector.http.address=0.0.0.0:7474
```

- To install the software on a server separate from the database, uncomment this:
```
dbms.connector.bolt.address=0.0.0.0:7687
```

- Browse to the database http://localhost:7474 and set a password (takes a few minutes to startup).
- Configure ~/netgrph/docs/netgraph.ini with your DB password.
- Install json, yaml, pymysql, py2neo and neo4j-bolt packages:
```
sudo pip3 install -r requirements.txt
```
- Import the sample network: `./test/first_import.sh`
- Run `./ngupdate.py -v -full` a couple more times to seed the network topology
- Browse to the database web interface and run `MATCH (s:Switch) RETURN s`
- Try out some sample commands

## Sample netgrph for use with test data
```
./netgrph.py abc4mdf
./netgrph.py abc4mdf -o csv
./netgrph.py abc4mdf -o json
./netgrph.py abc4mdf -o yaml
./netgrph.py -sp abc2sw1 xyz2sw1
./netgrph.py -sp abc.* xyz.*
./netgrph.py 120
./netgrph.py 1246
./netgrph.py -fp 10.1.120.50 8.8.8.8
./netgrph.py -nlist test_group
./netgrph.py -nlist test_group -o tree
./netgrph.py -group ABC
```

## Sample Reporting (to be expanded)
./ngreport.py -vlans


### Production Install

- I would add a netgrph user to your system and clone the repo under that user
- If you have a Cisco network, see the datasources/ directory file for parsing information
- At the top of the files, you can configure your config locations and extensions.
- See the update_parse.py and update_csv_from_netdb.sh scripts to see how I gather my data from netdb and stored configs.
- Consider installing NetDB for access to the Neighbor Discovery Data (I hope to find an alternative soon)
- Consider using something like Rancid or [Oxidized](https://github.com/ytti/oxidized) for gathering configurations from your devices.
- Create symlinks to netgrph.py, ngupdate.py and ngreport.py under /usr/local/bin/
- Make sure all users can read your config file and consider installing it under /etc/netgrph.ini (preferred)
- Consider changing your log location to /var/log/nglib.log and make sure all users have access to write to this file
- Schedule cron jobs under the netgrph user to update regularly (Full NetDB integration example)
```
01,16,31,46 *    * * * /home/yantisj/netgrph/prod/datasources/update_csv_from_netdb.sh
22          *    * * * /home/yantisj/netgrph/prod/datasources/update_parse.sh
02,17,32,48 *    * * * /home/yantisj/netgrph/prod/ngupdate.py -full
12          *    * * * /home/yantisj/netgrph/prod/ngupdate.py -unetdb
```
- Periodically clear node caches as they expire (adding -v will only show you what's expired)
```
ngupdate --clearEdges --hours 12
ngupdate --clearNodes --hours 12
```

## Adding firewalls and third-party devices
- Examine the csv files in csv/ to understand the required datasources for importing third-party data
- Examine the cyp/buildfw.cyp for understanding how to insert a L2 firewall between VRFs
- Examine the cyp/sample-queries.cyp to start querying the Neo4j database directly for data
