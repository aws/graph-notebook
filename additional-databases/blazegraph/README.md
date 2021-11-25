## Connecting graph notebook to Blazegraph SPARQL Endpoint

[Blazegraph](https://blazegraph.com/) is an open-source, high-performance RDF triple/quadstore graph-database that can be queried via a SPARQL endpoint.

For instructions on setting up and running Blazegraph locally, refer to the [Blazegraph Quickstart](https://github.com/blazegraph/database/wiki/Quick_Start) guide.

After local setup of Blazegraph is complete, set the following configuration to connect from graph-notebook:

```
%%graph_notebook_config

{
  "host": "localhost",
  "port": 9999,
  "ssl": false,
  "sparql": {
      "path": "sparql"
  }
}
```

Blazegraph also supports use of namespaces, which are used to refer to multiple triple or quad stores that are hosted in the same Blazegraph instance, and can be queried independently.

To direct SPARQL queries executed from `graph-notebook` to a specific namespace, you can specify the namespace path in your config:

```
%%graph_notebook_config

{
  "host": "localhost",
  "port": 9999,
  "ssl": false,
  "sparql": {
    "path": "blazegraph/namespace/foo/sparql"
  }
}
```

This will result in the url `localhost:9999/blazegraph/namespace/foo/sparql` being used when executing any `%%sparql` magic commands.



