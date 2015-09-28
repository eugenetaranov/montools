#!/usr/bin/env python

import psutil
from requests import post, exceptions
from socket import getfqdn

URL = 'http://{0}:8086/write?db={1}'
DBNAME = 'metrics'
DEBUG = False
INFLUXDB_SERVERS = ['10.2.0.2', '10.2.0.3']


def sendData(data):
    for host in INFLUXDB_SERVERS:
        try:
            post(URL.format(host, DBNAME), data=data, timeout=1)
        except exceptions.Timeout:
            if DEBUG: print 'Connection to {0} timed out'.format(host)
            continue

def main():

    hostname = getfqdn()
    data = ''

    for k, v in psutil.cpu_times_percent(interval=0.5)._asdict().iteritems():
        data += '{0}.cpu.{1} value={2}\n'.format(hostname, k, v)

    for k, v in psutil.virtual_memory()._asdict().iteritems():
        data += '{0}.mem.{1} value={2}\n'.format(hostname, k, v)

    for k, v in psutil.swap_memory()._asdict().iteritems():
        data += '{0}.swap.{1} value={2}\n'.format(hostname, k, v)

    du = { mp.mountpoint: psutil.disk_usage(mp.mountpoint).percent for mp in psutil.disk_partitions() }
    for k, v in du.iteritems():
        data += '{0}.du_percent.{1} value={2}\n'.format(hostname, k, v)

    for k, v in psutil.disk_io_counters(perdisk=True).iteritems():
        for m, p in v._asdict().iteritems():
            data += '{0}.io.{1}.{2} value={3}\n'.format(hostname, k, m, p)

    for k, v in psutil.net_io_counters(pernic=True).iteritems():
        for m, p in v._asdict().iteritems():
            data += '{0}.net.{1}.{2} value={3}\n'.format(hostname, k, m, p)

    connections = map(lambda x: x.status.lower(), psutil.net_connections())
    connections = map( lambda x: 'unknown_state' if x == 'none' else x, connections )
    for conn in set(connections):
        data += '{0}.netstat.{1} value={2}\n'.format(hostname, conn, connections.count(conn))

    if DEBUG: print data
    sendData(data)


if __name__ == '__main__':
    main()
