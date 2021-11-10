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
person_table = 'person'

# Create Gremlin client

gremlin_endpoints = GlueNeptuneConnectionInfo(args['AWS_REGION'], args['CONNECT_TO_NEPTUNE_ROLE_ARN']).neptune_endpoints(args['NEPTUNE_CONNECTION_NAME'])
gremlin_client = GlueGremlinClient(gremlin_endpoints)

# Create Phone vertices
# Create Email vertices
# Create City vertices
# Create Country vertices
# Create Person vertices

# 1. Get data from source SQL database
datasource0 = glueContext.create_dynamic_frame.from_catalog(database = database, table_name = person_table, transformation_ctx = "datasource0")

# datasource1 = glueContext.create_dynamic_frame.from_catalog(database = database, table_name = product_category_table, transformation_ctx = "datasource1")
# datasource2 = datasource0.join( ["CATEGORY_ID"],["CATEGORY_ID"], datasource1, transformation_ctx = "join")

# 2. Map fields to bulk load CSV column headings format

applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("id", "string", "id:String", "string"), 
    ("name", "string", "name:String", "string"), ("phone", "string", "phone:String", "string"), 
    ("email", "string", "email:String", "string"), ("city", "string", "city:String", "string"), ("country", "string", "country:String", "string"),
    ("pincode", "string", "pincode:String", "string"),("joineddate", "string", "joineddate:String", "string"), ("updateddate", "string", "updateddate:String", "string")], transformation_ctx = "applymapping1")

# 3. create user vertices

userDF = SelectFields.apply(frame = applymapping1, paths = ["id:String","name:String","joineddate:String","updateddate:String","email:String"], transformation_ctx = "userDF")
userDF = GlueGremlinCsvTransforms.create_prefixed_columns(userDF, [('~id', 'id:String','user')])
userDF.toDF().foreachPartition(gremlin_client.upsert_vertices('User', batch_size=100))

# 4. create phone vertices

phoneDF = SelectFields.apply(frame = applymapping1, paths = ["phone:String"], transformation_ctx = "phoneDF")
phoneDF = GlueGremlinCsvTransforms.create_prefixed_columns(phoneDF, [('~id', 'phone:String','phone')])
phoneDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Phone', batch_size=100))

# 5. create city vertices

cityDF = SelectFields.apply(frame = applymapping1, paths = ["city:String"], transformation_ctx = "cityDF")
cityDF = GlueGremlinCsvTransforms.create_prefixed_columns(cityDF, [('~id', 'city:String','city')])
cityDF.toDF().foreachPartition(gremlin_client.upsert_vertices('City', batch_size=100))

# 6. create country vertices
countryDF = SelectFields.apply(frame = applymapping1, paths = ["country:String"], transformation_ctx = "countryDF")
countryDF = GlueGremlinCsvTransforms.create_prefixed_columns(countryDF, [('~id', 'country:String','country')])
countryDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Country', batch_size=100))

# 7. create user to phone edges

userToPhoneMapping = SelectFields.apply(frame = applymapping1, paths = ["id:String","phone:String"], transformation_ctx = "userToPhoneMapping")
userToPhoneMapping = GlueGremlinCsvTransforms.create_prefixed_columns(userToPhoneMapping, [('~from', 'id:String','user'),('~to', 'phone:String','phone')])
userToPhoneMapping = GlueGremlinCsvTransforms.create_edge_id_column(userToPhoneMapping, '~from', '~to')
userToPhoneMapping.toDF().foreachPartition(gremlin_client.upsert_edges('hasPhone', batch_size=100))
    
# 8. create user to city edges

userToCityMapping = SelectFields.apply(frame = applymapping1, paths = ["id:String","city:String"], transformation_ctx = "userToCityMapping")
userToCityMapping = GlueGremlinCsvTransforms.create_prefixed_columns(userToCityMapping, [('~from', 'id:String','user'),('~to', 'city:String','city')])
userToCityMapping = GlueGremlinCsvTransforms.create_edge_id_column(userToCityMapping, '~from', '~to')
userToCityMapping.toDF().foreachPartition(gremlin_client.upsert_edges('inCity', batch_size=100))

# 9. create city to country edges

cityToCountryMapping = SelectFields.apply(frame = applymapping1, paths = ["city:String","country:String"], transformation_ctx = "cityToCountryMapping")
cityToCountryMapping = GlueGremlinCsvTransforms.create_prefixed_columns(cityToCountryMapping, [('~from', 'city:String','city'),('~to', 'country:String','country')])
cityToCountryMapping = GlueGremlinCsvTransforms.create_edge_id_column(cityToCountryMapping, '~from', '~to')
cityToCountryMapping.toDF().foreachPartition(gremlin_client.upsert_edges('inCountry', batch_size=100))



# End

# datasource0.printSchema()
# applymapping1.printSchema()
# phoneDF.printSchema()
# cityToCountyrMapping.show()
# userToPhoneMapping.show()
# userToCityMapping.show()
# cityToCountryMapping.show()

# countryDF.show()

# job.commit()

print("Done")
