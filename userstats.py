#!/usr/bin/env python

import os
from time import sleep, strftime
from pwd import getpwuid
from argparse import ArgumentParser
from pymongo import MongoClient
from socket import gethostname
from datetime import datetime
from re import sub

_CLOCK_TICKS = os.sysconf("SC_CLK_TCK")
stats, stats_red = {}, {}
mongoserver = '127.0.0.1'
mongoport = 27017
database = 'usagedata'
hostname = sub('-', '', gethostname().split('.')[0])
sleeptime = 60
threshold = 5

class Process:
    def __init__(self, pid):
        self.pid = pid
        try:
            statusf = open('/proc/%s/status' % self.pid)
        except IOError:
            self.name = ''
            self.uid = '0'
            statusf = 0
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
    if not params['verbose']:
        db = MongoClient(mongoserver, mongoport)[database]
        collection = db[hostname]
        rec = {'date': datetime.now(), 'data': stats_red }
        collection.insert(rec)
    stats, stats_red = {}, {}

def run():
    i = 0
    while True:
        if i > threshold:
            reduce();
            if params['verbose']: print stats_red
            flush(); i = 0
        get_rusage()
        i = i + 1
        sleep(sleeptime)

def _main():
    global stats
    if not params['daemonize']:
        run()
    else:
        pass


if __name__ == '__main__':
    params = parseargs()
    _main()
