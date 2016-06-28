#image: elasticsearch:1.7.1
FROM java:8-jre

MAINTAINER Nhat Nguyen <nminhnhat2008@gmail.com>

ENV DEBIAN_FRONTEND noninteractive

# grab gosu for easy step-down from root
RUN gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN curl -o /usr/local/bin/gosu -SL "https://github.com/tianon/gosu/releases/download/1.2/gosu-$(dpkg --print-architecture)" \
    && curl -o /usr/local/bin/gosu.asc -SL "https://github.com/tianon/gosu/releases/download/1.2/gosu-$(dpkg --print-architecture).asc" \
    && gpg --verify /usr/local/bin/gosu.asc \
    && rm /usr/local/bin/gosu.asc \
    && chmod +x /usr/local/bin/gosu

# Python YAML is required to generate ElasticSearch's configuration. Maven & JDK are
# needed to build the elasticsearch-zookeeper plugin.
RUN apt-get update &&\
    # apt-get -y install python-yaml python-setuptools maven git openjdk-7-jdk &&\
    apt-get -y install python-yaml &&\
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --keyserver ha.pool.sks-keyservers.net --recv-keys 46095ACC8548582C1A2699A9D27D666CD88E42B4

ENV ELASTICSEARCH_VERSION 1.7.1

RUN echo "deb http://packages.elasticsearch.org/elasticsearch/${ELASTICSEARCH_VERSION%.*}/debian stable main" > /etc/apt/sources.list.d/elasticsearch.list

ENV PATH /usr/share/elasticsearch/bin:$PATH

RUN apt-get update \
    && apt-get install elasticsearch=$ELASTICSEARCH_VERSION \
    && mkdir -p /usr/share/elasticsearch/config \
    && rm -rf /var/lib/apt/lists/* &&\
    # Install Marvel plugin
    plugin -v -i elasticsearch/marvel/latest

# COPY config /usr/share/elasticsearch/config

# Install ZooKeeper discovery plugin
RUN plugin -url https://github.com/grmblfrz/elasticsearch-zookeeper/releases/download/v1.7.1/elasticsearch-zookeeper-1.7.1.zip -install zookeeper
RUN git clone https://github.com/grmblfrz/elasticsearch-zookeeper.git /tmp/elasticsearch-zookeeper &&\
     cd /tmp/elasticsearch-zookeeper &&\
     mvn package -Dmaven.test.skip=true -Dzookeeper.version=3.4.6 &&\
     plugin -v -u file:///elasticsearch-zookeeper/target/releases/elasticsearch-zookeeper-1.7.1.zip \
     -i elasticsearch-zookeeper-1.7.1 &&\
     rm -rf /tmp/elasticsearch-zookeeper &&\
     # Install Marvel plugin
     plugin -v -i elasticsearch/marvel/latest &&\
     # Install AWS Cloud plugin
     plugin -v -i elasticsearch/elasticsearch-cloud-aws/2.7.0

VOLUME /usr/share/elasticsearch/data

COPY run.py /
COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]

# Java clients talk to the cluster over port 9300, using the native Elasticsearch transport protocol
# All other languages can communicate with Elasticsearch over port 9200 using a RESTful API
EXPOSE 9200 9300

############# Run this on host machine #############
# Elasticsearch also uses a mix of NioFS and MMapFS for the various files. Ensure that the maximum map count so that there is ample virtual memory available for mmapped files.
# RUN sysctl -w vm.max_map_count=262144

CMD ["elasticsearch"]