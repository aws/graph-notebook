## Connecting graph notebook to local Fuseki Endpoint

A quite lightweight SPARQL endpoint to play locally is [Apache Fuseki](https://jena.apache.org/documentation/fuseki2/index.html).

Fuseki provides separate endpoints for each configured dataset. 
For instance, if a dataset named `ds` has been defined in Fuseki, the corresponding SPARQL endpoint will be available from `http://localhost:3030/ds/sparql`.

Thus, it is necessary to define the path to the dataset's SPARQL endpoint in the `sparql.path` part of the configuration,
like in the following example that connects to `http://localhost:3030/ds/sparql`:

```
%%graph_notebook_config
{
  "host": "localhost",
  "port": 3030,
  "auth_mode": "DEFAULT",
  "iam_credentials_provider_type": "ROLE",
  "load_from_s3_arn": "",
  "ssl": false,
  "aws_region": "",
  "sparql": {
    "path": "ds/sparql"
  }
}
```
