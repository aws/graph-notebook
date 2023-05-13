import sys, boto3, os

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.transforms import ApplyMapping
from awsglue.transforms import RenameField
from awsglue.transforms import SelectFields
from awsglue.transforms import Filter
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import lit
from pyspark.sql.functions import format_string
from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.traversal import *
from neptune_python_utils.glue_neptune_connection_info import GlueNeptuneConnectionInfo
from neptune_python_utils.glue_gremlin_client import GlueGremlinClient
from neptune_python_utils.glue_gremlin_csv_transforms import GlueGremlinCsvTransforms
from neptune_python_utils.endpoints import Endpoints
from neptune_python_utils.gremlin_utils import GremlinUtils

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'DATABASE_NAME', 'NEPTUNE_CONNECTION_NAME', 'AWS_REGION', 'CONNECT_TO_NEPTUNE_ROLE_ARN'])
sc = SparkContext()
glueContext = GlueContext(sc)
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
database = args['DATABASE_NAME']
user_telemetry_table = 'telemetry'

# Create Gremlin client
gremlin_endpoints = GlueNeptuneConnectionInfo(args['AWS_REGION'], args['CONNECT_TO_NEPTUNE_ROLE_ARN']).neptune_endpoints(args['NEPTUNE_CONNECTION_NAME'])
gremlin_client = GlueGremlinClient(gremlin_endpoints)

# 1. Get data from source SQL database
datasource0 = glueContext.create_dynamic_frame.from_catalog(database = database, table_name = user_telemetry_table, transformation_ctx = "datasource0")

# 2. Map fields to bulk load CSV column headings format
applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("session_id", "string", "session_id:String", "string"), 
    ("user_id", "string", "user_id:String", "string"), ("user_agent", "string", "user_agent:String", "string"), 
    ("ip_address", "string", "ip_address:String", "string"), ("siteid", "string", "siteid:String", "string"),("pageid", "string", "pageid:String", "string"), ("session_start", "string", "session_start:String", "string")], transformation_ctx = "applymapping1")

# 3. create session vertices
sessionDF = SelectFields.apply(frame = applymapping1, paths = ["session_id:String"], transformation_ctx = "sessionDF")
sessionDF = GlueGremlinCsvTransforms.create_prefixed_columns(sessionDF, [('~id', 'session_id:String','session_id')])
sessionDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Session', batch_size=100))

# 4. create IP address vertices
ipDF = SelectFields.apply(frame = applymapping1, paths = ["ip_address:String"], transformation_ctx = "ipDF")
ipDF = GlueGremlinCsvTransforms.create_prefixed_columns(ipDF, [('~id', 'ip_address:String','ip_address')])
ipDF.toDF().foreachPartition(gremlin_client.upsert_vertices('IPAdress', batch_size=100))

# 5. create page vertices
pageDF = SelectFields.apply(frame = applymapping1, paths = ["pageid:String"], transformation_ctx = "pageDF")
pageDF = GlueGremlinCsvTransforms.create_prefixed_columns(pageDF, [('~id', 'pageid:String','pageid')])
pageDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Page', batch_size=100))

# 6. create user agent vertices
useragentDF = SelectFields.apply(frame = applymapping1, paths = ["user_agent:String"], transformation_ctx = "useragentDF")
useragentDF = GlueGremlinCsvTransforms.create_prefixed_columns(useragentDF, [('~id', 'user_agent:String','user_agent')])
useragentDF.toDF().foreachPartition(gremlin_client.upsert_vertices('UserAgent', batch_size=100))

# 7. create session to user edges
userToSessionMapping = SelectFields.apply(frame = applymapping1, paths = ["user_id:String","session_id:String",'session_start:String'], transformation_ctx = "userToSessionMapping")
#fetch records with valid user ids 
userToSessionMapping = Filter.apply(frame = userToSessionMapping, f = lambda x: x["user_id:String"] not in [""])
userToSessionMapping = GlueGremlinCsvTransforms.create_prefixed_columns(userToSessionMapping, [('~to', 'user_id:String','user'),('~from', 'session_id:String','session_id'),('session_start', 'session_start:String','session_start')])
userToSessionMapping = GlueGremlinCsvTransforms.create_edge_id_column(userToSessionMapping, '~from', '~to')
userToSessionMapping.toDF().foreachPartition(gremlin_client.upsert_edges('linkedTo', batch_size=100))

# 8. create session to user_agent mapping
sessionToUserAgentMapping = SelectFields.apply(frame = applymapping1, paths = ["session_id:String","user_agent:String"], transformation_ctx = "sessionToUserAgentMapping")
sessionToUserAgentMapping = GlueGremlinCsvTransforms.create_prefixed_columns(sessionToUserAgentMapping, [('~from', 'session_id:String','session_id'),('~to', 'user_agent:String','user_agent')])
sessionToUserAgentMapping = GlueGremlinCsvTransforms.create_edge_id_column(sessionToUserAgentMapping, '~from', '~to')
sessionToUserAgentMapping.toDF().foreachPartition(gremlin_client.upsert_edges('usedDevice', batch_size=100))

# 9. create session to ip address mapping
sessionToIPAddressMapping = SelectFields.apply(frame = applymapping1, paths = ["session_id:String","ip_address:String"], transformation_ctx = "sessionToIPAddressMapping")
sessionToIPAddressMapping = GlueGremlinCsvTransforms.create_prefixed_columns(sessionToIPAddressMapping, [('~from', 'session_id:String','session_id'),('~to', 'ip_address:String','ip_address')])
sessionToIPAddressMapping = GlueGremlinCsvTransforms.create_edge_id_column(sessionToIPAddressMapping, '~from', '~to')
sessionToIPAddressMapping.toDF().foreachPartition(gremlin_client.upsert_edges('lastSeenAt', batch_size=100))

# 10. create session to page Id mapping
sessionToPageMapping = SelectFields.apply(frame = applymapping1, paths = ["session_id:String","pageid:String"], transformation_ctx = "sessionToPageMapping")
sessionToPageMapping = GlueGremlinCsvTransforms.create_prefixed_columns(sessionToPageMapping, [('~from', 'session_id:String','session_id'),('~to', 'pageid:String','pageid')])
sessionToPageMapping = GlueGremlinCsvTransforms.create_edge_id_column(sessionToPageMapping, '~from', '~to')
sessionToPageMapping.toDF().foreachPartition(gremlin_client.upsert_edges('viewed', batch_size=100))

job.commit()
print("Done")
