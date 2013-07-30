from feedly.storage.cassandra.connection import get_cassandra_connection
from pycassa.system_manager import SystemManager, SIMPLE_STRATEGY
import random

import logging
from pycassa.types import IntegerType
from pycassa.columnfamily import ColumnFamily
from pycassa.cassandra.ttypes import ConsistencyLevel
from django.conf import settings
from gevent import monkey, pool
import gevent
import time
print 'monkey patching by gevent'
monkey.patch_all()
print 'done'
try:
    # ignore this if we already configured settings
    settings.configure()
except RuntimeError, e:
    pass


logger = logging.getLogger(__name__)


def handle():

    FEEDLY_CASSANDRA_HOSTS = [
        'ec2-54-247-128-192.eu-west-1.compute.amazonaws.com',
        'ec2-54-216-163-72.eu-west-1.compute.amazonaws.com',
        'ec2-54-216-108-200.eu-west-1.compute.amazonaws.com',
    ]
    sys = SystemManager(FEEDLY_CASSANDRA_HOSTS[0])

    keyspace_name = 'benchmark_cassandra_%s' % random.randint(0, 10000)

    print 'setting up the new keyspace'
    sys.create_keyspace(
        keyspace_name, SIMPLE_STRATEGY, {'replication_factor': '1'}
    )
    time.sleep(1)

    print 'setting up the column family benchmark'
    sys.create_column_family(
        keyspace_name, 'benchmark', comparator_type=IntegerType(reversed=True)
    )
    logger.info('inserting random data till we drop')
    time.sleep(1)

    '''
    Try:
    - a batch interface
    - gevent
    - different consistency levels
    '''
    connection = get_cassandra_connection(
        keyspace_name, FEEDLY_CASSANDRA_HOSTS)

    column_family = ColumnFamily(
        connection,
        'benchmark',
        write_consistency_level=ConsistencyLevel.ANY
    )
    client = column_family

    print 'setting up the test data'
    activity_keys = range(3000, 3005)
    activity_data = ['a' * 34] * len(activity_keys)
    activities = dict(zip(activity_keys, activity_data))
    print activities

    print 'starting pool'
    worker_pool = pool.Pool(5)

    def insert_data(activities):
        key = 'row:%s' % x
        columns = {int(k): str(v) for k, v in activities.iteritems()}
        client.insert(key, columns)

    for x in range(1000000):
        worker_pool.spawn(insert_data, activities)

    while len(worker_pool):
        gevent.sleep(1)


if __name__ == '__main__':
    handle()
