## Ansible NetGrph Playbooks

These playbooks will install Ansible on Ubuntu 14.04 or 16.04 for
you. It will not set your database password or configure your
netgrph.ini file for now, so you need to do that manually. Once the
scripts run, browse to http://machine:7474 and setup your
password. Set that same password in /home/netgrph/docs/netgrph.ini,
and run the /home/netgrph/test/first_import.sh.

### Running Ansible via localhost


```
apt-get install ansible
echo [netgrph] >> /etc/ansible/hosts
echo localhost ansible_connection=local >> /etc/ansible/hosts
```

#### Run ansible on localhost

```
git clone https://github.com/yantisj/netgrph.git /tmp/netgrph/
cd /tmp/netgrph/docs/playbooks/
ansible-playbook netgrph.yml --ask-sudo-pass
```
