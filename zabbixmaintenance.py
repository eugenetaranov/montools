#!/usr/bin/env python

import sys
import zabbix_api
from os import _exit


zabbix = '127.1'
zabbixuser = 'user'
zabbixpasswd = 'passwd'
zabbixurl = 'https://%s/api_jsonrpc.php' % zabbix
domain = 'example.com'
description = 'Doing backup'


def main( action, host ):
    zapi = zabbix_api.ZabbixAPI(server = zabbixurl)
    zapi.login(user = zabbixuser, password = zabbixpasswd)
    maintenanceid = 0
    if not zapi.test_login(): _exit(2)
    hostid = zapi.host.get( {'filter': { 'host': '%s.%s' % (host, domain) }}  )[0]['hostid']
    try:
        maintenanceid = zapi.maintenance.get( { 'hostids': [ hostid ], 'search': { 'name': 'Backup-%s' % host }} )[0]['maintenanceid']
    except IndexError:
        pass
    if action == 'on':
        if maintenanceid > 0:
            zapi.maintenance.delete( [ maintenanceid ] )
        zapi.maintenance.create( { 'name': 'Backup-%s' % host, 'hostids': [ hostid ], 'timeperiods': [ { 'timeperiod_type': 0 } ], 'description': description } )
        _exit(0)
    elif action == 'off':
        if maintenanceid > 0:
            zapi.maintenance.delete( [ maintenanceid ] )
        _exit(0)
    _exit(4)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print '''Usage: %s <action> <hostname>
action: on, off''' % sys.argv[0]
        _exit(5)
    main( sys.argv[1], sys.argv[2] )
