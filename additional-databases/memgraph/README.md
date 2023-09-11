## Connecting graph notebook to Memgraph Bolt Endpoint

[Memgraph](https://memgraph.com/) is an open-source in-memory graph database built for highly performant and advanced analytical insights. Memgraph is Neo4J Bolt protocol compatible and it uses the standardized Cypher query language. 

For a quick start, run the following command in your terminal to start Memgraph Platform in a Docker container: 

```
docker run -it -p 7687:7687 -p 7444:7444 -p 3000:3000 -e MEMGRAPH="--bolt-server-name-for-init=Neo4j/" memgraph/memgraph-platform
```

The above command started Memgraph database, MAGE (graph algorithms library) and Memgraph Lab (visual user interface). For additional instructions on setting up and running Memgraph locally, refer to the [Memgraph documentation](https://memgraph.com/docs/memgraph/installation). Connection to the graph notebook works if the `--bolt-server-name-for-init` setting is modified. For more information on changing configuration settings, refer to our [how-to guide](https://memgraph.com/docs/memgraph/how-to-guides/config-logs).


After local setup of Memgraph is complete, set the following configuration to connect from graph-notebook:

```
%%graph_notebook_config
{
  "host": "localhost",
  "port": 7687,
  "ssl": false
}
```

If you set up an authentication on your Memgraph instance, you can provide login details via configuration. For example, if you created user `username` identified by `password`, then the following configuration is the correct one:

%%graph_notebook_config
{
  "host": "localhost",
  "port": 7687,
  "ssl": false,
  "memgraph": {
    "username": "username",
    "password": "password",
    "auth": true
  }
}

To learn how to manage users in Memgraph, refer to [Memgraph documentation](https://memgraph.com/docs/memgraph/reference-guide/users).

You can query Memgraph via Bolt protocol which was designed for efficient communication with graph databases. Memgraph supports versions 1 and 4 of the protocol. Ensure that you specify the `%%oc bolt` option when submitting queries to the Bolt endpoint. For example, a correct way of running a Cypher query via Bolt protocol is:

```
%%oc bolt
MATCH (n)
RETURN count(n)
```

Another way of ensuring that Memgraph is running, head to `localhost:3000` and check out Memgraph Lab, a visual user interface. You can see node and relationship count there, explore, query and visualize data. If you get stuck and have more questions, [let's talk at Memgraph Discord community](https://www.discord.gg/memgraph).
