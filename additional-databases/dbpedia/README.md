## Connecting graph notebook to DBPedia SPARQL Endpoint

The official SPARQL endpoint for DBPedia is available from https://dbpedia.org/sparql and is based on a Virtuoso engine.

It is possible to connect to this endpoint using the following configuration:

```
%%graph_notebook_config
{
  "host": "dbpedia.org",
  "port": 443,
  "ssl": true,
  "sparql": {
      "path": "sparql"
  }
}
```
