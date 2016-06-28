#!/usr/bin/env python

# Inspire from SignalFuse, Inc.
# https://github.com/signalfuse/docker-elasticsearch

# Generate configs for ElasticSearch.
# Requires python-yaml for configuration writing.

import os
import yaml
import socket


ELASTICSEARCH_CONFIG_FILE = '/usr/share/elasticsearch/config/elasticsearch.yml'
ELASTICSEARCH_LOGGING_CONFIG = '/usr/share/elasticsearch/config/logging.yml'
DEFAULT_ELASTICSEARCH_ZONE = 'ether'
LOG_PATTERN = "%d{yyyy'-'MM'-'dd'T'HH:mm:ss.SSSXXX} %-5p [%-35.35t] [%-36.36c]: %m%n"

def env_as_bool(k, default=True):
    if k in os.environ:
        v = os.environ[k].lower()
        return v == 'true'
    return default

# Prepare the YAML configuration and write it.
with open(ELASTICSEARCH_CONFIG_FILE, 'w+') as conf:
    data = {
        'cluster': {
            'name': os.environ.get('CLUSTER_NAME',
                                   '{}-elasticsearch'.format('local')),
            # configure the zone attribute as one of the awareness allocation attributes
            # a shard and its replica will not be allocated in the same zone
            # exception is when the cluster is left with less zone values than shard
            'routing.allocation.awareness.attributes': 'zone',

            # Shard allocation, at any point in time only 2 shards are allowed to be moving
            'routing.allocation.cluster_concurrent_rebalance': 2,

            # Shard allocation will take free disk space into account while allocating shards to a node
            # prevent shard allocation on nodes depending on disk usage
            'routing.allocation.disk.threshold_enabled': True,
            'routing.allocation.disk.watermark.low': '85%',

            # Relocate shards to another node if the node disk usage rises above
            'routing.allocation.disk.watermark.high': '90%',
        },

        # Node configuration
        'node': {
            #'name': socket.gethostname(),
            'name': os.environ.get('NODE_NAME'),
            'zone': os.environ.get('ZONE_NAME', DEFAULT_ELASTICSEARCH_ZONE),
            # Allow this node to store data (enabled by default):
            'data': env_as_bool('IS_DATA_NODE'),
            # If you want this node to never become a master node, only to hold data, set to false
            'master': env_as_bool('IS_MASTER_NODE'),
        },

        'path': {
            # Can optionally include more than one location, favouring locations with most free space on creation
            'data': os.environ.get('PATH_DATA', '/usr/share/elasticsearch/data').split(','),
            'logs': '/var/log/docker/elasticsearch',
        },

        'gateway': {
            # Wait nodes to come online, the data would have been local and nothing would need to move
            # After the first node is up, begin recovering after 5 minutes
            'recover_after_time': '5m',
        },

        # Network and discovery.
        'network': {
            # Set the address other nodes will use to communicate with this node.
            'publish_host': os.environ.get('CONTAINER_HOST_ADDRESS'),
        },

        # Index/replica configuration
        'index': {
            'number_of_replicas': int(os.environ.get('NUM_INDEX_REPLICAS', 1)),
            'number_of_shards': int(os.environ.get('NUM_INDEX_SHARDS', 5)),

            # SlowQueries log
            'search.slowlog.threshold.query.warn': '10s',
            'search.slowlog.threshold.query.info': '5s',
            'search.slowlog.threshold.query.debug': '2s',
            'search.slowlog.threshold.query.trace': '500ms',

            'search.slowlog.threshold.fetch.warn': '1s',
            'search.slowlog.threshold.fetch.info': '800ms',
            'search.slowlog.threshold.fetch.debug': '500ms',
            'search.slowlog.threshold.fetch.trace': '200ms',

            'indexing.slowlog.threshold.index.warn': '10s',
            'indexing.slowlog.threshold.index.info': '5s',
            'indexing.slowlog.threshold.index.debug': '2s',
            'indexing.slowlog.threshold.index.trace': '500ms',
        },

        # port for the node to node communication (9300 by default):
        'transport.tcp.port': os.environ.get('TRANSPORT_TCP_PORT', 9300),

        'http': {
            # Enable REST API
            # All other languages can communicate with Elasticsearch
            'enabled': env_as_bool('HTTP_ENABLED'),
            'port': os.environ.get('HTTP_PORT', 9200),
        },

        'discovery': {
            'type': 'zen',

            # Disable multicast
            'zen.ping.multicast.enabled': False,

            'zen.ping.unicast.hosts': os.environ.get('UNICAST_HOSTS', []).split(','),

            # Fault detection settings
            'zen.fd.ping_interval': '15s',
            'zen.fd.ping_timeout': '30s',
            'zen.fd.ping_retries': 5,
        },

        # Marvel plugin configuration.
        'marvel': {
            'agent': {
                # enable Marvel plugin agent reporting from this instance (Disable on the monitoring instance, avoid collecting data from the monitoring instance itself)
                'enabled': env_as_bool('MARVEL_ENABLED'),

                # TODO: improve this, ideally we want to figure this out
                # automatically.
                # Tell each node where to send its stats
                # Can have multiple monitoring instances
                # Data will be sent to the first host, but will failover to the next host(s) if the first is not reachable
                'exporter.es.hosts': \
                    os.environ.get('MARVEL_TARGETS', 'localhost:9200').split(','),
            },
        },

        # AWS Cloud plugin configuration.
        'cloud': {
            'aws': {
                'region': os.environ.get('ZONE_NAME', DEFAULT_ELASTICSEARCH_ZONE),
            },
        },

        ################## OPTIMIZATION ##################

        # Disable dynamic scripting and prevent remote code execution
        # watch here (http://bouk.co/blog/elasticsearch-rce/)
        # 'script.disable_dynamic': True,

        # New version of Elasticsearch support fine-grained
        # Fine-grained script settings (separate inline and indexed script)
        'script': {
            'inline': 'off',
            'indexed': 'off',
        },

        'bootstrap': {
            # Lock the process address space into RAM, 
            # preventing any Elasticsearch memory from being swapped out
            'mlockall': True,
        },

        'action': {
            # disable allowing to delete indices via wildcards or _all
            'destructive_requires_name': True,
        },

        'indices': {
            # data cache used mainly when sorting on or faceting on a field.
            # It loads all the field values to memory in order to provide fast document based access to those values.
            'fielddata.cache.size': '25%',

            # make the index request more efficient
            'cluster.send_refresh_mapping': False,
        },
    }
    
    # using get will return 'None' if a key is not present rather than raise a 'KeyError'
    if os.environ.get('AWS_ACCESS_KEY') and os.environ.get('AWS_SECRET_KEY'):
        data['cloud']['aws'].update({
            'access_key': os.environ['AWS_ACCESS_KEY'],
            'secret_key': os.environ['AWS_SECRET_KEY'],
        })

    yaml.dump(data, conf, default_flow_style=False)

# Setup the logging configuration
with open(ELASTICSEARCH_LOGGING_CONFIG, 'w+') as conf:
    yaml.dump({
        'es.logger.level': 'INFO',

        # output messages into a rolling log file
        'rootLogger': '${es.logger.level},R',
        'logger': {
            # log action execution errors
            'action': 'DEBUG',

            # reduce the logging for aws, too much is logged under the default INFO
            'com.amazonaws': 'WARN',
        },
        'appender': {
            'R': {
                'type': 'rollingFile',
                'File': '${path.logs}/%s.log' % 'elasticsearch',
                'MaxFileSize': '100MB',
                'MaxBackupIndex': '10',
                'layout': {
                  'type': 'pattern',
                  'ConversionPattern': LOG_PATTERN,
                },
            },
        },
    }, conf, default_flow_style=False)
