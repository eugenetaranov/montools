#!/usr/bin/env python


from pymongo import MongoClient, ReadPreference
from pymongo.errors import *
from datetime import datetime
from sys import exit
from time import sleep


MONGODB_URI = 'mongodb://mongodb-0:27017,mongodb-1:27017,mongodb-2:27017/?readPreference=secondary'
REPLICASET = ''
DB = 'monitoring'
COLLECTION = 'monitoring'
WAIT = 5


class MongoConnect(object):
    def __init__(self, uri, port=27017, replicaset=None):
        self.conn = MongoClient(uri, port, replicaSet=replicaset)
        try:
            self.conn.server_info()
        except ServerSelectionTimeoutError:
            return None


if __name__ == '__main__':

    conn = MongoConnect(uri=MONGODB_URI, replicaset=REPLICASET)

    if conn:
        collection = conn.conn[DB][COLLECTION]

    post = {'message': datetime.utcnow()}
    id = collection.insert(post)

    sleep(WAIT)

    if collection.find_one({'_id': id}):
        collection.remove({'_id': id})

        if len(conn.conn.secondaries) >= 2:
            print 'Replication OK'
            exit(0)
        else:
            print 'Replication OK, but too few slaves is online'
            exit(1)

    else:
        print 'Replication FAIL'
        exit(2)
