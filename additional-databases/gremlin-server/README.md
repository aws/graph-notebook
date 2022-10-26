## Connecting graph-notebook to a Gremlin Server

![Gremlin](https://github.com/aws/graph-notebook/blob/main/images/gremlin-notebook.png?raw=true, "Picture of Gremlin holding a notebook")

These notes explain how to connect the graph-notebook to a Gremlin server running locally on the same machine. The same steps should also work if you have a remote Gremlin Server. In such cases `localhost` should be replaced with the DNS or IP address of the remote server. It is assumed the [graph-notebook installation](https://github.com/aws/graph-notebook/blob/main/README.md) has been completed and the Jupyter environment is running before following these steps.

### Gremlin Server Configuration
Several of the steps below are optional but please read each step carefully and decide if you want to apply it.
1. Download the Gremlin Server from https://tinkerpop.apache.org/ and unzip it. The remaining steps in this section assume you have made your working directory the place where you performed the unzip.
2. In conf/tinkergraph-empty.properties, change the ID manager from `LONG` to `ANY` to
   enable IDs that include text strings.
   ```
   gremlin.tinkergraph.vertexIdManager=ANY
   ```
3. Optionally add another line doing the same for edge IDs.
   ```
   gremlin.tinkergraph.edgeIdManager=ANY

   ```
4. To enable HTTP as well as Web Socket connections to the Gremlin Server, edit the file /conf/gremlin-server.yaml and change
   ```
   channelizer: org.apache.tinkerpop.gremlin.server.channel.WebSocketChannelizer
   ```
   to
   ```
    channelizer: org.apache.tinkerpop.gremlin.server.channel.WsAndHttpChannelizer
   ```
   This will allow you to access the Gremlin Server from Jupyter using commands like `curl` as well as using the `%%gremlin` cell magic. This step is optional if you do not need HTTP connectivity to the server.
5. Start the Gremlin server `bin/gremlin-server.sh start`


### Connecting to a local Gremlin Server from Jupyter
1. In the Jupyter Notebook disable SSL using `%%graph_notebook_config` and change the host to `localhost`. Keep the other defaults even though they are not used for configuring the Gremlin Server.
```
%%graph_notebook_config
{
  "host": "localhost",
  "port": 8182,
  "ssl": false,
  "gremlin": {
    "traversal_source": "g",
    "username": "",
    "password": "",
    "message_serializer": "graphsonv3"
  }
}
```
If the Gremlin Server you wish to connect to is remote,  replacing `localhost` with the IP address or DNS of the remote server should work. This assumes you have access to that server from your local machine.

### Using `%seed` with Gremlin Server
The graph-notebook has a `%seed` command that can be used to load sample data. For some data sets to load successfully, the stack size used by the Gremlin Server needs to be increased. If you do not plan to use the `%seed` command to load the `air-routes` data set this step can be ignored.

1. In order to load the `airports` data set into TinkerGraph via Gremlin Server using the graph-notebook `%seed` command, the size of the JVM thread stack needs to be increased. Editing the `gremlin-server.sh` file and adding `-Xss2m` to the JAVA_OPTIONS variable is one way to do that. Locate this section of the file and add the `-Xss2m` flag.

  ```
  # Set Java options
  if [[ "$JAVA_OPTIONS" = "" ]] ; then
      JAVA_OPTIONS="-Xms512m -Xmx4096m -Xss2m"
  fi
  ```
