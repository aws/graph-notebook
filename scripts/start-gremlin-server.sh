rm -rf /tmp/apache-tinkerpop-gremlin-server*
pkill -f gremlin-server

curl https://downloads.apache.org/tinkerpop/3.4.10/apache-tinkerpop-gremlin-server-3.4.10-bin.zip -o /tmp/apache-tinkerpop-gremlin-server.zip
unzip /tmp/apache-tinkerpop-gremlin-server.zip -d /tmp/
export JAVA_OPTIONS="-Xms512m -Xmx4096m -Xss2m"


echo $'' >> /tmp/apache-tinkerpop-gremlin-server-3.4.10/conf/tinkergraph-empty.properties
echo "gremlin.tinkergraph.edgeIdManager=ANY" >> /tmp/apache-tinkerpop-gremlin-server-3.4.10/conf/tinkergraph-empty.properties
sed -i '' 's/vertexIdManager=LONG/vertexIdManager=ANY/g' /tmp/apache-tinkerpop-gremlin-server-3.4.10/conf/tinkergraph-empty.properties
sed -i '' 's/WebSocketChannelizer/WsAndHttpChannelizer/g' /tmp/apache-tinkerpop-gremlin-server-3.4.10/conf/gremlin-server.yaml

/tmp/apache-tinkerpop-gremlin-server-3.4.10/bin/gremlin-server.sh start

echo '{
  "host": "localhost",
  "port": 8182,
  "auth_mode": "DEFAULT",
  "iam_credentials_provider_type": "ROLE",
  "load_from_s3_arn": "",
  "ssl": false,
  "aws_region": "us-east-1"
}' > /tmp/graph_notebook_config_integration_test.json