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
user_transactions_table = 'transactions'

# Create Gremlin client
gremlin_endpoints = GlueNeptuneConnectionInfo(args['AWS_REGION'], args['CONNECT_TO_NEPTUNE_ROLE_ARN']).neptune_endpoints(args['NEPTUNE_CONNECTION_NAME'])
gremlin_client = GlueGremlinClient(gremlin_endpoints)

# 1. Get data from source SQL database
datasource0 = glueContext.create_dynamic_frame.from_catalog(database = database, table_name = user_transactions_table, transformation_ctx = "datasource0")

# 2. Map fields to bulk load CSV column headings format
applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("transaction_id", "string", "transaction_id:String", "string"), 
    ("user_id", "string", "user_id:String", "string"), ("product_id", "string", "product_id:String", "string"), 
    ("product_name", "string", "product_name:String", "string"), ("purchased_date", "string", "purchased_date:String","string"),("review", "string", "review:String","string")], transformation_ctx = "applymapping1")

# 3. create product vertices
productDF = SelectFields.apply(frame = applymapping1, paths = ["product_id:String","product_name:String"], transformation_ctx = "productDF")
productDF = GlueGremlinCsvTransforms.create_prefixed_columns(productDF, [('~id', 'product_id:String','product')])
productDF.toDF().foreachPartition(gremlin_client.upsert_vertices('Product', batch_size=100))

# 4. create user to product edges
userToProductMapping = SelectFields.apply(frame = applymapping1, paths = ["user_id:String","product_id:String","purchased_date:String"], transformation_ctx = "userToProductMapping")
userToProductMapping = GlueGremlinCsvTransforms.create_prefixed_columns(userToProductMapping, [('~from', 'user_id:String','user'),('~to', 'product_id:String','product')])
userToProductMapping = GlueGremlinCsvTransforms.create_edge_id_column(userToProductMapping, '~from', '~to')
userToProductMapping.toDF().foreachPartition(gremlin_client.upsert_edges('purchased', batch_size=100))

job.commit()
print("Done")
