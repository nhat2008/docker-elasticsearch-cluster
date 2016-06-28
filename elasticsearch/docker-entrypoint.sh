#!/bin/bash

# Create log folder
if [ ! -d "/var/log/docker/elasticsearch" ]; then
    mkdir -p /var/log/docker/elasticsearch
    chown -R elasticsearch:elasticsearch /var/log/docker/elasticsearch
fi

set -e

# Generate configuration
./run.py

# Require privileged
# allow user running Elasticsearch to lock memory
# to be able to set mlockall=true
ulimit -l unlimited

# Add elasticsearch as command if needed
if [ "${1:0:1}" = '-' ]; then
    set -- elasticsearch "$@"
fi

# Drop root privileges if we are running elasticsearch
if [ "$1" = 'elasticsearch' ]; then
    # Change the ownership of /usr/share/elasticsearch/data to elasticsearch
    chown -R elasticsearch:elasticsearch /usr/share/elasticsearch/data
    exec gosu elasticsearch "$@"
fi

# As argument is not related to elasticsearch,
# then assume that user wants to run his own process,
# for example a `bash` shell to explore this image
exec "$@"