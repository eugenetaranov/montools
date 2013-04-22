#!/usr/bin/env python

import os, sys
import ConfigParser
from time import sleep, strftime
from pwd import getpwuid
from pymongo import MongoClient
from socket import gethostname
from datetime import datetime
from re import sub
from daemon import Daemon

_CLOCK_TICKS = os.sysconf("SC_CLK_TCK")
stats, stats_red = {}, {}
mongoserver, mongoport, database, sleeptime, threshold = [0] * 5
hostname = sub('-', '', gethostname().split('.')[0])
pidfile = '/var/run/monitor.pid'
configfile = '/etc/monitor/monitor.conf'

class Process:
    def __init__(self, pid):
        self.pid = pid
        try:
            statusf = open('/proc/%s/status' % self.pid)
        except IOError:
            self.name = ''
            self.uid = '0'
            statusf = 0
        self.vmsize, self.vmrss = [0] * 2
        if statusf:
            for line in statusf:
                if line.startswith('Name:'): self.name = line.split()[1]
                if line.startswith('Uid:'): self.uid = line.split()[1]
                if line.startswith('VmSize:'):
                    self.vmsize = int(line.split()[1])
                if line.startswith('VmRSS:'):
                    self.vmrss = int(line.split()[1])
            statusf.close()
        try:
            statf = open('/proc/%s/stat' % self.pid)
        except IOError:
            statf, self.cpu_usr, self.cpu_sys = [0] * 3
        if statf:
            stat = statf.read().split(' '); statf.close()
            self.cpu_usr = float(stat[13]) / _CLOCK_TICKS
            self.cpu_sys = float(stat[14]) / _CLOCK_TICKS
            statf.close()
        try:
            iof = open('/proc/%s/io' % self.pid)
        except IOError:
            iof, self.ops_read, self.ops_write, self.bytes_read, self.bytes_write = [0] * 5
        if iof:
            for line in iof:
                if line.startswith('syscr:'): self.ops_read = line.split()[1]
                if line.startswith('syscw:'): self.ops_write = line.split()[1]
                if line.startswith('read_bytes:'): self.bytes_read = int(line.split()[1])
                if line.startswith('write_bytes:'): self.bytes_write = int(line.split()[1])
            iof.close()

def getuid(uid):
    user = getpwuid(int(uid))[0]
    return user

def configparse():
    config = ConfigParser.SafeConfigParser()
    config.read(configfile)
    global mongoserver, mongoport, database, sleeptime, threshold
    mongoserver = config.get('general', 'mongoserver')
    mongoport = config.getint('general', 'mongoport')
    database = config.get('general', 'database')
    sleeptime = config.getint('general', 'sleeptime')
    threshold = config.getint('general', 'threshold')

def parseargs():
    p = ArgumentParser()
    p.add_argument('-d', '--daemonize', action = 'store_true')
    p.add_argument('-v', '--verbose', action = 'store_true')
    return vars(p.parse_args())

def get_rusage():
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    global stats
    for pid in pids:
        proc = Process(pid)
        uid = proc.uid
        if uid not in stats:
            stats[uid] = {}
        if pid not in stats[uid]:
            stats[proc.uid][pid] = {}
            stats[uid][pid]['cpu_usr'], stats[uid][pid]['cpu_sys'], stats[uid][pid]['mem_rss'], stats[uid][pid]['mem_vms'] = [0] * 4
        stats[uid][pid]['cpu_usr'] = proc.cpu_usr
        stats[uid][pid]['cpu_sys'] = proc.cpu_sys
        stats[uid][pid]['mem_rss'] = (stats[uid][pid]['mem_rss'] + proc.vmrss) * 0.7
        stats[uid][pid]['mem_vms'] = (stats[uid][pid]['mem_vms'] + proc.vmsize) * 0.7
        stats[uid][pid]['io_bytes_r'] = proc.bytes_read
        stats[uid][pid]['io_bytes_w'] = proc.bytes_write

def reduce():
    global stats, stats_red
    for uid in stats:
        stats_red[uid] = {}
        stats_red[uid]['cpu_usr'], stats_red[uid]['cpu_sys'], stats_red[uid]['mem_rss'], stats_red[uid]['mem_vms'] = [0] * 4
        stats_red[uid]['io_bytes_r'], stats_red[uid]['io_bytes_w'] = [0] * 2
        stats_red[uid]['user'] = getuid(uid)
        for pid in stats[uid]:
            stats_red[uid]['cpu_usr'] = stats_red[uid]['cpu_usr'] + stats[uid][pid]['cpu_usr']
            stats_red[uid]['cpu_sys'] = stats_red[uid]['cpu_sys'] + stats[uid][pid]['cpu_sys']
            stats_red[uid]['mem_rss'] = stats_red[uid]['mem_rss'] + stats[uid][pid]['mem_rss']
            stats_red[uid]['mem_vms'] = stats_red[uid]['mem_vms'] + stats[uid][pid]['mem_vms']
            stats_red[uid]['io_bytes_r'] = stats_red[uid]['io_bytes_r'] + stats[uid][pid]['io_bytes_r']
            stats_red[uid]['io_bytes_w'] = stats_red[uid]['io_bytes_w'] + stats[uid][pid]['io_bytes_w']

def flush():
    global stats, stats_red
    db = MongoClient(mongoserver, mongoport)[database]
    collection = db[hostname]
    rec = {'date': datetime.now(), 'data': stats_red }
    collection.insert(rec)
    stats, stats_red = {}, {}

class Monitor(Daemon):
    def run(self):
        configparse()
        i = 0
        while True:
            if i > threshold:
                reduce();
                flush(); i = 0
            get_rusage()
            i = i + 1
            sleep(sleeptime)


if __name__ == '__main__':
    srv = Monitor(pidfile)
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            srv.start()
        elif sys.argv[1] == 'stop':
            srv.stop()
        elif sys.argv[1] == 'restart':
            srv.restart()
        else:
            print 'Unknown command'
            sys.exit(2)
        sys.exit(0)
    else:
        print 'Usage %s start|stop|restart' % sys.argv[0]
        sys.exit(2)
