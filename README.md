## Graph Notebook: easily query and visualize graphs 

The graph notebook provides an easy way to interact with graph databases using Jupyter notebooks. Using this open-source Python package, you can connect to any graph database that supports the [Apache TinkerPop](https://tinkerpop.apache.org/) or the [RDF SPARQL](https://www.w3.org/TR/rdf-sparql-query/) graph model. These databases could be running locally on your desktop or in the cloud. Graph databases can be used to explore a variety of use cases including [knowledge graphs](https://aws.amazon.com/neptune/knowledge-graphs-on-aws/) and [identity graphs](https://aws.amazon.com/neptune/identity-graphs-on-aws/).

### Visualizing Gremlin queries:

![Gremlin query and graph](./images/GremlinQueryGraph.png)

### Visualizing SPARQL queries:

![SPARL query and graph](./images/SPARQLQueryGraph.png)

Instructions for connecting to the following graph databases:

|             Endpoint            |       Graph model       |   Query language    |
| :-----------------------------: | :---------------------: | :-----------------: | 
|[Gremlin Server](#gremlin-server)|     property graph      |       Gremlin       |
|    [Blazegraph](#blazegraph)    |            RDF          |       SPARQL        |
|[Amazon Neptune](#amazon-neptune)|  property graph or RDF  |  Gremlin or SPARQL  |

We encourage others to contribute configurations they find useful. There is an [`additional-databases`](https://github.com/aws/graph-notebook/blob/main/additional-databases) folder where more information can be found.

## Features

#### Notebook cell 'magic' extensions in the IPython 3 kernel
`%%sparql` - Executes a SPARQL query against your configured database endpoint.

`%%gremlin` - Executes a Gremlin query against your database using web sockets. The results are similar to what the Gremlin console would return.

**TIP** :point_right:  There is syntax highlighting for both `%%sparql` and `%%gremlin` queries to help you write good code.

#### Notebook cell 'magic' extensions in the IPython 3 kernel
`%graph_notebook_config` - Returns a JSON object that contains connection information for your host.

`%query_mode` - Lets you set the query mode for your queries to one of:

* `query` (the default) : executes the query against the normal SPARQL or Gremlin endpoint
* `explain` : Returns an explanation of the query plan instead of the query's results (valid for both SPARQL and Gremlin).
* `profile` : Returns a profile of the query's operation, but does not actually execute the query (valid only for Gremlin).

`%seed` - Provides a form to add data to your graph without the use of a bulk loader. both SPARQL and Gremlin have an airport routes dataset.

**TIP** :point_right: You can list all the magics installed in the Python 3 kernel using the `%lsmagic` command.


## Prerequisites

You will need:

* [Python](https://www.python.org/downloads/) 3.6.1-3.6.12
* [Jupyter Notebook](https://jupyter.org/install) 5.7.10
* [Tornado](https://pypi.org/project/tornado/) 4.5.3
* A graph database that provides a SPARQL 1.1 Endpoint or a Gremlin Server


## Installation

```
# pin specific versions of Jupyter and Tornado dependency
pip install notebook==5.7.10
pip install tornado==4.5.3

# install the package
pip install graph-notebook

# install and enable the visualization widget
jupyter nbextension install --py --sys-prefix graph_notebook.widgets
jupyter nbextension enable  --py --sys-prefix graph_notebook.widgets

# copy static html resources
python -m graph_notebook.static_resources.install
python -m graph_notebook.nbextensions.install

# copy premade starter notebooks
python -m graph_notebook.notebooks.install --destination ~/notebook/destination/dir  

# start jupyter
jupyter notebook ~/notebook/destination/dir
```

## Connecting to a graph database

### Gremlin Server 

In a new cell in the Jupyter notebook, change the configuration using `%%graph_notebook_config` and modify the fields for `host`, `port`, and `ssl`.  For a local Gremlin server (HTTP or WebSockets), you can use the following command:

```
%%graph_notebook_config
{
  "host": "localhost",
  "port": 8182,
  "auth_mode": "DEFAULT",
  "iam_credentials_provider_type": "ROLE",
  "load_from_s3_arn": "",
  "ssl": false,
  "aws_region": "us-east-1"
}
```

To setup a new local Gremlin Server for use with the graph notebook, check out [`additional-databases/gremlin server`](additional-databases/gremlin-server)

### Blazegraph

Change the configuration using `%%graph_notebook_config` and modify the fields for `host`, `port`, and `ssl`. For a local Blazegraph database, you can use the following command:

```
%%graph_notebook_config
{
  "host": "localhost",
  "port": 9999,
  "auth_mode": "DEFAULT",
  "iam_credentials_provider_type": "ROLE",
  "load_from_s3_arn": "",
  "ssl": false,
  "aws_region": "us-east-1"
}
```
To setup a new local Blazegraph database for use with the graph notebook, check out the [Quick Start](https://github.com/blazegraph/database/wiki/Quick_Start) from Blazegraph.

### Amazon Neptune

Change the configuration using `%%graph_notebook_config` and modify the defaults as they apply to your Neptune cluster:

```
%%graph_notebook_config
{
  "host": "your-neptune-endpoint",
  "port": 8182,
  "auth_mode": "DEFAULT",
  "iam_credentials_provider_type": "ENV",
  "load_from_s3_arn": "",
  "ssl": true,
  "aws_region": "your-neptune-region"
}
```
To setup a new Amazon Neptune cluster, check out the [AWS documentation](https://docs.aws.amazon.com/neptune/latest/userguide/manage-console-launch.html).

When connecting the graph notebook to Neptune, make sure you have a network setup to communicate to the VPC that Neptune runs on. If not, you can follow [this guide](https://github.com/aws/graph-notebook/tree/main/additional-databases/neptune). 

## Authentication (Amazon Neptune)

If you are running a SigV4 authenticated endpoint, ensure that the config field `iam_credentials_provider_type` is set
to `ENV` and that you have set the following environment variables:

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- AWS_SESSION_TOKEN (OPTIONAL. Use if you are using temporary credentials)


## Contributing Guidelines

See [CONTRIBUTING](https://github.com/aws/graph-notebook/blob/main/CONTRIBUTING.md) for more information.

## License

This project is licensed under the Apache-2.0 License.
