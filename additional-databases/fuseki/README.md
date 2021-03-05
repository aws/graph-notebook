## Connecting graph-notebook to a local Apache Fuseki Endpoint

[Apache Fuseki](https://jena.apache.org/documentation/fuseki2/index.html) is a lightweight SPARQL 1.1 endpoint that is easy to setup locally. Check out the [Fuseki Quickstart](https://jena.apache.org/documentation/fuseki2/fuseki-quick-start.html) for setup instructions.

Fuseki provides separate endpoints for each configured dataset. For instance, if a dataset named `ds` has been defined in Fuseki, the corresponding SPARQL endpoint will be available from `http://localhost:3030/ds/sparql`.

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
