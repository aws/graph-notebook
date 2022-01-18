rm -rf /tmp/apache-tinkerpop-gremlin-server*
pkill -f gremlin-server

curl https://downloads.apache.org/tinkerpop/3.5.2/apache-tinkerpop-gremlin-console-3.5.2-bin.zip -o /tmp/apache-tinkerpop-gremlin-server.zip
unzip /tmp/apache-tinkerpop-gremlin-server.zip -d /tmp/
echo "gremlin.graph=org.apache.tinkerpop.gremlin.tinkergraph.structure.TinkerGraph
gremlin.tinkergraph.vertexIdManager=ANY
gremlin.tinkergraph.edgeIdManager=ANY" > /tmp/apache-tinkerpop-gremlin-server-3.5.2/conf/tinkergraph-empty.properties

echo "host: $(hostname -i)
port: 8182
evaluationTimeout: 30000
channelizer: org.apache.tinkerpop.gremlin.server.channel.WsAndHttpChannelizer
graphs: {
  graph: conf/tinkergraph-empty.properties}
scriptEngines: {
  gremlin-groovy: {
    plugins: { org.apache.tinkerpop.gremlin.server.jsr223.GremlinServerGremlinPlugin: {},
               org.apache.tinkerpop.gremlin.tinkergraph.jsr223.TinkerGraphGremlinPlugin: {},
               org.apache.tinkerpop.gremlin.jsr223.ImportGremlinPlugin: {classImports: [java.lang.Math], methodImports: [java.lang.Math#*]},
               org.apache.tinkerpop.gremlin.jsr223.ScriptFileGremlinPlugin: {files: [scripts/empty-sample.groovy]}}}}
serializers:
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GryoMessageSerializerV3d0, config: { ioRegistries: [org.apache.tinkerpop.gremlin.tinkergraph.structure.TinkerIoRegistryV3d0] }}            # application/vnd.gremlin-v3.0+gryo
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GryoMessageSerializerV3d0, config: { serializeResultToString: true }}                                                                      # application/vnd.gremlin-v3.0+gryo-stringd
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerV3d0, config: { ioRegistries: [org.apache.tinkerpop.gremlin.tinkergraph.structure.TinkerIoRegistryV3d0] }}        # application/json
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphBinaryMessageSerializerV1 }                                                                                                           # application/vnd.graphbinary-v1.0
  - { className: org.apache.tinkerpop.gremlin.driver.ser.GraphBinaryMessageSerializerV1, config: { serializeResultToString: true }}                                                                 # application/vnd.graphbinary-v1.0-stringd
processors:
  - { className: org.apache.tinkerpop.gremlin.server.op.session.SessionOpProcessor, config: { sessionTimeout: 28800000 }}
  - { className: org.apache.tinkerpop.gremlin.server.op.traversal.TraversalOpProcessor, config: { cacheExpirationTime: 600000, cacheMaxSize: 1000 }}
metrics: {
  consoleReporter: {enabled: true, interval: 180000},
  csvReporter: {enabled: true, interval: 180000, fileName: /tmp/gremlin-server-metrics.csv},
  jmxReporter: {enabled: true},
  slf4jReporter: {enabled: true, interval: 180000}}
strictTransactionManagement: false
idleConnectionTimeout: 0
keepAliveInterval: 0
maxInitialLineLength: 4096
maxHeaderSize: 8192
maxChunkSize: 8192
maxContentLength: 65536
maxAccumulationBufferComponents: 1024
resultIterationBatchSize: 64
writeBufferLowWaterMark: 32768
writeBufferHighWaterMark: 65536
ssl: {
  enabled: false}" > /tmp/apache-tinkerpop-gremlin-server-3.5.2/conf/gremlin-server.yaml

echo "tinkergraph-empty.properties:"
cat /tmp/apache-tinkerpop-gremlin-server-3.5.2/conf/tinkergraph-empty.properties

echo "gremlin-server.yaml:"
cat /tmp/apache-tinkerpop-gremlin-server-3.5.2/conf/gremlin-server.yaml

echo "{
  \"host\": \"$(hostname -i)\",
  \"port\": 8182,
  \"auth_mode\": \"DEFAULT\",
  \"iam_credentials_provider_type\": \"ROLE\",
  \"load_from_s3_arn\": \"\",
  \"ssl\": false,
  \"aws_region\": \"us-east-1\"
}" > /tmp/graph_notebook_config_integration_test.json