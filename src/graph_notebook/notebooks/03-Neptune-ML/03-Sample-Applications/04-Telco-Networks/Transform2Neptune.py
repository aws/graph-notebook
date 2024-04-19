import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import pyspark.sql.functions as f


## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

def transform_edges(spark, s3_path: str, s3_dest: str, max_from: int = -1):
    _, basename = s3_path.rsplit('/', 1)
    basename = basename.split('.')[0]
    _, fro, verb, to = basename.split('_')

    df = (
            spark.read.format("com.databricks.spark.csv")
            .option("header", "false")
            .option("inferSchema", "true")
            .load(s3_path)
        )
    columns = df.columns
    label = f"{fro}_{verb}_{to}"
    names = ["~from", "~to"] + [f"{label}_attr_{i}:Float" for i in range(len(columns) - 2)]
    df = df.toDF(*names)
    if max_from > 0:
        df = df.where(df["~from"] < f.lit(max_from))
    df = df.withColumn("~label", f.lit(label))
    df = df.withColumn("~from",f.concat_ws("_", f.lit(fro), df["~from"]))
    df = df.withColumn("~to", f.concat_ws("_", f.lit(fro), df["~to"]))
    df = df.withColumn("~id", f.concat_ws("_", f.lit(label), f.monotonically_increasing_id()))
    columns = list(df.columns)
    columns.remove("~id")
    df = df.select("~id", *columns)
    df.write.format("com.databricks.spark.csv").option("header", "true").save(s3_dest)

def transform_nodes(spark, s3_path: str, s3_dest: str, max_node: int = -1):
    _, basename = s3_path.rsplit('/', 1)
    basename = basename.split('.')[0]
    _, label = basename.split('_')

    df = (
            spark.read.format("com.databricks.spark.csv")
            .option("header", "false")
            .option("inferSchema", "true")
            .load(s3_path)
        )
    columns = df.columns
    names = ["~id"] + [f"{label}_attr_{i}:Float" for i in range(len(columns) - 1)]
    df = df.toDF(*names)
    if max_node > 0:
        df = df.where(df["~id"] < f.lit(max_node))
    df = df.withColumn("~label", f.lit(label))
    df = df.withColumn("~id", f.concat_ws("_", f.lit(label), df["~id"]))
    df.write.format("com.databricks.spark.csv").option("header", "true").save(s3_dest)

transform_nodes(spark,"s3://pathtoyourdata/node_user.txt", "s3://pathtoyourdata/node_user.csv")
transform_nodes(spark,"s3://apathtoyourdata/node_cell.txt", "s3://pathtoyourdata/node_cell.csv")


transform_edges(spark,"s3://pathtoyourdata/edge_user_live_cell.txt", "s3://pathtoyourdata/edges_user_live_cell.csv")



job = Job(glueContext)
job.init(args['JOB_NAME'], args)
job.commit()