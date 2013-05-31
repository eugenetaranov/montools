#!/usr/bin/env python

import os, random, string, subprocess
from sys import argv, exit
from time import time
from socket import gethostname


LOCALDIR = '/tmp'
REMOTEDIR = '/mnt/media'
RWSIZE = 1024000
ZBXSENDER = '/usr/bin/zabbix_sender'
ZBXSERVER = 'zabbixmaster.local'
DEBUG = 0

results = {}

def genrandom(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(length))

def writebin(fname, length):
    with open(fname, 'wb') as fout:
        fout.write(os.urandom(length))

def readbin(fname, length):
    with open(fname, 'r') as fin:
        fin.read(length)

def getstat(fname):
    os.stat(fname)

def timeit(typeTest, func):
    global results
    start = time()
    func()
    stop = time()
    results[typeTest] = round(stop - start, 4)
    return 0

def directorylist(path):
    os.listdir(path)

def main(dir):
    fname = '%s/%s' % (dir, genrandom(10))
    timeit('write', lambda: writebin(fname, RWSIZE))
    timeit('read', lambda: readbin(fname, RWSIZE))
    timeit('listdir', lambda: directorylist('/var/log'))
    timeit('stat', lambda: getstat(fname))
    if DEBUG: print fname, results['write'], results['read'], results['listdir'], results['stat']
    os.unlink(fname)
    try:
        with open('/dev/null', 'w') as dnull:
            for key in results.keys():
                subprocess.check_call([ ZBXSENDER, '-z', ZBXSERVER, '-s', gethostname(),
                    '-k', 'io.report.%s[%s]' % (key, argv[1]), '-o', str(results[key]) ], stdout = dnull)
    except subprocess.CalledProcessError as e:
        if DEBUG: print e
        return()
    exit(0)


if __name__ == '__main__':
    if argv[1] == 'local': main(LOCALDIR)
    if argv[1] == 'remote': main(REMOTEDIR)
    exit(1)
