#!/usr/bin/env python

import logging, logging.handlers
from os import uname
from urllib2 import urlopen
from json import load
from random import sample
from sys import argv, exit


LOG_FILE = "/var/log/solrreplicationcheck.log"
STATUS_URL = "http://%s:%s/solr/admin/cores?action=STATUS&wt=json"
DETAILS_URL = "http://%s:%s/solr/%s/replication?command=details&wt=json"
DEBUG = 0

class solrCoreHandler:
    """solr core handler"""
    def __init__(self, host, port, core):
        self.slaveServer = host
        self.slavePort = port
        self.name = core

    def _getMasterServer(self):
        try:
            doc = load(urlopen(DETAILS_URL % (self.slaveServer, self.slavePort, self.name)))
        except:
            raise
        self.masterServer, self.masterPort = doc['details']['slave']['masterUrl'].split("/")[2].split(":")

    def _getData(self, host, port):
        try:
            doc = load(urlopen(DETAILS_URL % (host, port, self.name)))
        except IOError, e:
            if DEBUG: print e
            exit(9999)
        return doc

    def getReplicationData(self):
        self._getMasterServer()
        slaveDoc = self._getData(self.slaveServer, self.slavePort)
        self.slaveIndex = slaveDoc["details"]["indexVersion"]
        self.slaveGeneration = slaveDoc["details"]["generation"]
        self.isReplicating = slaveDoc['details']['slave']['isReplicating']
        self.isPollingDisabled = slaveDoc['details']['slave']['isPollingDisabled']
        masterDoc = self._getData(self.masterServer, self.masterPort)
        self.masterIndex = masterDoc["details"]["indexVersion"]
        self.masterGeneration = masterDoc["details"]["generation"]

    def printData(self):
        return self.name, self.masterIndex, self.masterGeneration, self.slaveIndex, self.slaveGeneration


def getCores(host, port):
    try:
        doc = load(urlopen(STATUS_URL % (host, port)))['status']
    except IOError, e:
        if DEBUG: print e
        exit(9999)
    cores = []
    for core in doc:
        if core == 'core0': continue
        cores.append(core)
    return cores


def main(SOLR_SERVER, SOLR_PORT, NUM):
    RES = 0
    ##Logger
    logger = logging.getLogger('replication')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ##
    cores = sample(getCores(SOLR_SERVER, SOLR_PORT), NUM)
    for core in cores:
        solrCore = solrCoreHandler(SOLR_SERVER, SOLR_PORT, core)
        solrCore.getReplicationData()
        if solrCore.isReplicating != True and solrCore.isPollingDisabled != True:
            if solrCore.slaveIndex != solrCore.masterIndex or solrCore.slaveGeneration != solrCore.masterGeneration:
                RES +=1
                logger.error("Core:%s masterIndex:%s masterGeneration:%s slaveIndex:%s slaveGeneration:%s" % solrCore.printData())
        if DEBUG: print "Core:%s masterIndex:%s masterGeneration:%s slaveIndex:%s slaveGeneration:%s" % solrCore.printData()
    exit(RES)


if __name__ == '__main__':
    try:
        SOLR_SERVER, SOLR_PORT, NUM = argv[1:4]
    except ValueError:
        print "Given no valid solr server, port and number of cores to check"
        exit(9999)
    main(SOLR_SERVER, SOLR_PORT, int(NUM))
