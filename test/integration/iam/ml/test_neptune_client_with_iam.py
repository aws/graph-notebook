"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.configuration.generate_config import Configuration
from graph_notebook.neptune.client import Client

client: Client
config: Configuration

TEST_BULKLOAD_SOURCE = 's3://aws-ml-customer-samples-%s/bulkload-datasets/%s/airroutes/v01'
GREMLIN_TEST_LABEL = 'graph-notebook-test'
SPARQL_TEST_PREDICATE = '<http://test.com/p/graph-notebook-test>'
