import sys, boto3, os

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.transforms import ApplyMapping
from awsglue.transforms import RenameField
from awsglue.transforms import SelectFields
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
user_demographics_table = 'demographics'

# Create Gremlin client
gremlin_endpoints = GlueNeptuneConnectionInfo(args['AWS_REGION'], args['CONNECT_TO_NEPTUNE_ROLE_ARN']).neptune_endpoints(args['NEPTUNE_CONNECTION_NAME'])
gremlin_client = GlueGremlinClient(gremlin_endpoints)

# 1. Get data from source SQL database
datasource0 = glueContext.create_dynamic_frame.from_catalog(database = database, table_name = user_demographics_table, transformation_ctx = "datasource0")

# 2. Map fields to bulk load CSV column headings format
applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("id", "string", "id:String", "string"), 
    ("name", "string", "name:String", "string"), ("phone", "string", "phone:String", "string"), 
    ("email", "string", "email:String", "string"), ("city", "string", "city:String", "string"),("state", "string", "state:String", "string"), ("country", "string", "country:String", "string"),("address", "string", "address:String", "string"),
    ("pincode", "string", "pincode:String", "string"),("joineddate", "string", "joineddate:String", "string"), ("updateddate", "string", "updateddate:String", "string")], transformation_ctx = "applymapping1")

# 3. create user vertices
userDF = SelectFields.apply(frame = applymapping1, paths = ["id:String","name:String","joineddate:String","updateddate:String","email:String"], transformation_ctx = "userDF")
userDF = GlueGremlinCsvTransforms.create_prefixed_columns(userDF, [('~id', 'id:String','user')])
userDF.toDF().foreachPartition(gremlin_client.upsert_vertices('User', batch_size=100))

# 4. create phone vertices
phoneDF = SelectFields.apply(frame = applymapping1, paths = ["phone:String"], transformation_ctx = "phoneDF")
phoneDF = GlueGremlinCsvTransforms.create_prefixed_columns(phoneDF, [('~id', 'phone:String','phone')])
phoneDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Phone', batch_size=100))

# 5 create email vertices
emailDF = SelectFields.apply(frame = applymapping1, paths = ["email:String"], transformation_ctx = "emailDF")
emailDF = GlueGremlinCsvTransforms.create_prefixed_columns(emailDF, [('~id', 'email:String','email')])
emailDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Email', batch_size=100))

# 6. create city vertices
cityDF = SelectFields.apply(frame = applymapping1, paths = ["city:String"], transformation_ctx = "cityDF")
cityDF = GlueGremlinCsvTransforms.create_prefixed_columns(cityDF, [('~id', 'city:String','city')])
cityDF.toDF().foreachPartition(gremlin_client.upsert_vertices('City', batch_size=100))

# 7. create state vertices
stateDF = SelectFields.apply(frame = applymapping1, paths = ["state:String"], transformation_ctx = "stateDF")
stateDF = GlueGremlinCsvTransforms.create_prefixed_columns(stateDF, [('~id', 'state:String','state')])
stateDF.toDF().foreachPartition(gremlin_client.upsert_vertices('State', batch_size=100))

# 8. create country vertices
countryDF = SelectFields.apply(frame = applymapping1, paths = ["country:String"], transformation_ctx = "countryDF")
countryDF = GlueGremlinCsvTransforms.create_prefixed_columns(countryDF, [('~id', 'country:String','country')])
countryDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Country', batch_size=100))

# 9 create address vertices
addressDF = SelectFields.apply(frame = applymapping1, paths = ["address:String"], transformation_ctx = "addressDF")
addressDF = GlueGremlinCsvTransforms.create_prefixed_columns(addressDF, [('~id', 'address:String','address')])
addressDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Address', batch_size=100))

# 10. create user to phone edges
userToPhoneMapping = SelectFields.apply(frame = applymapping1, paths = ["id:String","phone:String"], transformation_ctx = "userToPhoneMapping")
userToPhoneMapping = GlueGremlinCsvTransforms.create_prefixed_columns(userToPhoneMapping, [('~from', 'id:String','user'),('~to', 'phone:String','phone')])
userToPhoneMapping = GlueGremlinCsvTransforms.create_edge_id_column(userToPhoneMapping, '~from', '~to')
userToPhoneMapping.toDF().foreachPartition(gremlin_client.upsert_edges('hasPhone', batch_size=100))

# 11. create user to email edges
userToEmailMapping = SelectFields.apply(frame = applymapping1, paths = ["id:String","email:String"], transformation_ctx = "userToEmailMapping")
userToEmailMapping = GlueGremlinCsvTransforms.create_prefixed_columns(userToEmailMapping, [('~from', 'id:String','user'),('~to', 'email:String','email')])
userToEmailMapping = GlueGremlinCsvTransforms.create_edge_id_column(userToEmailMapping, '~from', '~to')
userToEmailMapping.toDF().foreachPartition(gremlin_client.upsert_edges('hasEmail', batch_size=100))

# 12. create user to address edges
userToAddressMapping = SelectFields.apply(frame = applymapping1, paths = ["id:String","address:String"], transformation_ctx = "userToAddressMapping")
userToAddressMapping = GlueGremlinCsvTransforms.create_prefixed_columns(userToAddressMapping, [('~from', 'id:String','user'),('~to', 'address:String','address')])
userToAddressMapping = GlueGremlinCsvTransforms.create_edge_id_column(userToAddressMapping, '~from', '~to')
userToAddressMapping.toDF().foreachPartition(gremlin_client.upsert_edges('hasAddr', batch_size=100))

# 13. create address to city edges
addressToCityMapping = SelectFields.apply(frame = applymapping1, paths = ["address:String","city:String"], transformation_ctx = "addressToCityMapping")
addressToCityMapping = GlueGremlinCsvTransforms.create_prefixed_columns(addressToCityMapping, [('~from', 'address:String','address'),('~to', 'city:String','city')])
addressToCityMapping = GlueGremlinCsvTransforms.create_edge_id_column(addressToCityMapping, '~from', '~to')
addressToCityMapping.toDF().foreachPartition(gremlin_client.upsert_edges('inCity', batch_size=100))

# 14. create city to state edges
cityToStateMapping = SelectFields.apply(frame = applymapping1, paths = ["city:String","state:String"], transformation_ctx = "cityToStateMapping")
cityToStateMapping = GlueGremlinCsvTransforms.create_prefixed_columns(cityToStateMapping, [('~from', 'city:String','city'),('~to', 'state:String','state')])
cityToStateMapping = GlueGremlinCsvTransforms.create_edge_id_column(cityToStateMapping, '~from', '~to')
cityToStateMapping.toDF().foreachPartition(gremlin_client.upsert_edges('inState', batch_size=100))

# 15. create state to country edges
stateToCountryMapping = SelectFields.apply(frame = applymapping1, paths = ["state:String","country:String"], transformation_ctx = "stateToCountryMapping")
stateToCountryMapping = GlueGremlinCsvTransforms.create_prefixed_columns(stateToCountryMapping, [('~from', 'state:String','state'),('~to', 'country:String','country')])
stateToCountryMapping = GlueGremlinCsvTransforms.create_edge_id_column(stateToCountryMapping, '~from', '~to')
stateToCountryMapping.toDF().foreachPartition(gremlin_client.upsert_edges('inCountry', batch_size=100))

job.commit()
print("Done")
