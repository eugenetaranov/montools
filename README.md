montools
========

ldapcheck.py

Ldap check usage:
ldapcheck.py [-h] -s SERVER -p PORT -b BASEDN [--filter FILTER]
                    [--username USERNAME] [--password PASSWORD] [--secure]
                    [-t TIMEOUT] [-v]
optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
  -p PORT, --port PORT
  -b BASEDN, --basedn BASEDN
  --filter FILTER
  --username USERNAME
  --password PASSWORD
  --secure
  -t TIMEOUT, --timeout TIMEOUT
  -v, --verbose

zabbixmaintenance.py

Host maintenance in zabbix On/Off:
zabbixmaintenance.py SERVERNAME [on|off]

solrreplicationmonitoring.py

Returns number of cores with failed replication among the checked cores.
Usage:
solrreplicationcheck.py <SLAVE SOLR IP> <PORT> <NUM OF CORES TO CHECK>
