#!/usr/bin/env python

from subprocess import Popen
from sys import exit, path
import random, string, os
from time import sleep


TRACKEDPROCS = ['php-fpm',]
TRACKTIME = 300
STRACEDIR = '/tmp'

class Process:
    def __init__(self, pid):
        self.pid = pid
        try:
            statusf = open('/proc/%s/status' % self.pid)
        except IOError:
            self.name = ''
            self.state = ''
            statusf = 0
        if statusf:
            for line in statusf:
                if line.startswith('Name:'): self.name = line.split()[1]
                if line.startswith('State:'): self.state = line.split()[1]
            statusf.close()

def genrandom(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(length))

def getprocesses():
    trackedProc = {}
    trackedProc['running'] = []
    trackedProc['blocked'] = []
    trackedProc['sleeping'] = []
    trackedProc['zombie'] = []
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    for pid in pids:
        res = Process(pid)
        if res.state == 'R' and res.name in TRACKEDPROCS: trackedProc['running'].append(pid)
        if res.state == 'D' and res.name in TRACKEDPROCS: trackedProc['blocked'].append(pid)
        if res.state == 'S' and res.name in TRACKEDPROCS: trackedProc['sleeping'].append(pid)
        if res.state == 'Z' and res.name in TRACKEDPROCS: trackedProc['zombie'].append(pid)
    for key in trackedProc:
        if len(trackedProc[key]) < 2: trackedProc[key].extend(['9999999', '9999999'])
    return trackedProc

def runstrace(processes, stracefname):
    strace = Popen(['strace', '-f', '-p', processes['sleeping'][0], '-p', processes['sleeping'][1],
        '-p', processes['blocked'][0], '-p', processes['blocked'][1],
        '-p', processes['running'][0], '-o', stracefname])
    sleep(TRACKTIME)
    strace.kill()
    return 0


def main():
    processes = getprocesses()
    stracefname = '%s/%s.strace' % (STRACEDIR, genrandom(10))
    runstrace(processes, stracefname)
    exit(0)


if __name__ == '__main__':
    main()
