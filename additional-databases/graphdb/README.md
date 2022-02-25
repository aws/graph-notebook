## Connecting Graph Notebook to GraphDB SPARQL Endpoint

[GraphDB](https://graphdb.ontotext.com//) is a highly efficient and robust graph database with RDF and SPARQL support.

For instructions on setting up and running GraphDB locally, please refer to the [GraphDB Quickstart](https://graphdb.ontotext.com/documentation/standard/quick-start-guide.html) guide.

After the local setup of GraphDB is complete, use one of the following configurations to connect:

Queries:
```
%%graph_notebook_config

{
  "host": "localhost",
  "port": 7200,
  "ssl": false,
  "sparql": {
      "path": "repositories/<repository_id>"
  }
}
```

Updates:
```
%%graph_notebook_config

{
  "host": "localhost",
  "port": 7200,
  "ssl": false,
  "sparql": {
      "path": "repositories/<repository_id>/statements"
  }
}
```



