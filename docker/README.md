Run `%load_ext graph_notebook.magics` at the top of a notebook to enable gremlin magic like `%%gremlin`

Default password is `admin`.

## Example Runs

### On Linux:
- Note that these commands invoke [host networking mode](https://docs.docker.com/network/host/). This mode is only compatible with Linux, and may cause issues if run on a Mac or Windows host.

```sh
docker run --network="host" -p 8888:8888 -t graph-notebook

# Sharing directories
docker run --network="host" -p 8889:8889 -p 8888:8888 -v $(pwd)/out:/working 


# For connecting with IAM Auth
docker run -p 8888:8888 \
 -e AWS_ACCESS_KEY_ID \
 -e AWS_SECRET_ACCESS_KEY \ 
 -e AWS_SESSION_TOKEN \ 
 -e AWS_REGION="us-east-1" \
 graph-notebook
```

### On Mac/Windows:

```sh
docker run -p 8888:8888 -t graph-notebook

# Sharing directories
docker run -p 8889:8889 -p 8888:8888 -v $(pwd)/out:/working 

# For connecting with IAM Auth
docker run -p 8888:8888 \
 -e AWS_ACCESS_KEY_ID \
 -e AWS_SECRET_ACCESS_KEY \ 
 -e AWS_SESSION_TOKEN \ 
 -e AWS_REGION="us-east-1" \
 graph-notebook
```


## Post-Launch Configuration

Example Notebooks are placed in the `Example Notebooks` sub-directory.

Within the Jupyter Notebook you must configure the Notebook settings to account for `localhost` or `remote` connections.

### Example Localhost Connection

```ipynb
%%graph_notebook_config
    {
        "host": "localhost",
        "port": 8182,
        "ssl": false,
        // Proxy port can be defined without attempting to proxy
        "proxy_port":8182,
        "proxy_host": "",
        "auth_mode": "IAM",
        "aws_region": "us-east-1",
        "load_from_s3_arn": ""
    }
```

### Example Neptune Proxy Connection

```ipynb
    {
        "host": "clustername.cluster-ididididid.us-east-1.neptune.amazonaws.com",
        "port": 8182,
        "ssl": true,
        "proxy_port": 8182,
        "proxy_host": "host.proxy.com",
        "auth_mode": "IAM",
        "aws_region": "us-east-1",
        "load_from_s3_arn": ""
    }
```

## Configurable Properties

| Parameter      | Description |
| ----------- | ----------- |
| WORKING_DIR   | Where installation happens inside of container        |
| NOTEBOOK_DIR   | Where all Notebooks are held within the container        |
| EXAMPLE_NOTEBOOK_DIR   | Where automatically created Notebooks are created (Subfolder of NOTEBOOK_DIR)        |
| NODE_VERSION   | Version of Node used for visualizations        |
| GRAPH_NOTEBOOK_AUTH_MODE   | What type of auth should be used for connection to the Graph DB        |
| GRAPH_NOTEBOOK_HOST   | Host Graph Notebook will attempt to connect to for queries         |
| GRAPH_NOTEBOOK_PORT   | Port graph notebook will use to attempt connection to port        |
| NEPTUNE_LOAD_FROM_S3_ROLE_ARN   | Role Arn used for Data loads from S3        |
| AWS_REGION   | Region Neptune instance is located in AWS        |
| NOTEBOOK_PORT   | Port Jupyter Lab is listening on. (8888)        |
| LAB_PORT   | Port Jupyter Lab is listening on. (8889)        |
| GRAPH_NOTEBOOK_SSL   | Whether or not to use SSL for connections        |
| NOTEBOOK_PASSWORD   | Password to login into jupyter (default: admin)       |
| pipargs   | Arguments used during pip install        |
| PROVIDE_EXAMPLES   | Whether or not to automatically copy example notebooks over when a volume is being shared.        |
| GRAPH_NOTEBOOK_PROXY_HOST   | Host that will proxy requests to Neptune. Will not proxy if not provided.        |
| GRAPH_NOTEBOOK_PROXY_PORT   | Port for proxy host.        |
