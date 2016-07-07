## Ansible NetGrph Playbooks

These playbooks will install NetGrph via Ansible on Ubuntu 14.04 or 16.04 for
you. It will not set your database password or configure your netgrph.ini file
for now, so you need to do that manually. Once the scripts run, browse to
http://machine:7474 and setup your password. Set that same password in
/home/netgrph/docs/netgrph.ini, and run the /home/netgrph/test/first_import.sh.

#### Setting up Ansible to run via localhost

```
sudo su -
apt-get install ansible
echo '[netgrph]' >> /etc/ansible/hosts
echo localhost ansible_connection=local >> /etc/ansible/hosts
exit
```

#### Run playbooks against localhost (installs under netgrph user)

```
git clone https://github.com/yantisj/netgrph.git /tmp/netgrph/
cd /tmp/netgrph/docs/playbooks/
ansible-playbook netgrph.yml --ask-sudo-pass
```

#### Test the install

```
sudo su - netgrph
cd netgrph
```

##### Use an insecure DB password for testing (not recommended)
```
./test/set_neo4j_password.sh
```

##### Test a database import
```
./test/first_import.sh
```

- See the INSTALL.md file for test queries and production install information
