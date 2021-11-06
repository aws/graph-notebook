"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json

from graph_notebook.configuration.generate_config import DEFAULT_CONFIG_LOCATION, Configuration, AuthModeEnum, \
    SparqlSection, GremlinSection


def get_config_from_dict(data: dict) -> Configuration:
    sparql_section = SparqlSection(**data['sparql']) if 'sparql' in data else SparqlSection('')
    gremlin_section = GremlinSection(**data['gremlin']) if 'gremlin' in data else GremlinSection('')
    if "amazonaws.com" in data['host']:
        if gremlin_section.to_dict()['traversal_source'] != 'g':
            print('Ignoring custom traversal source, Amazon Neptune does not support this functionality.\n')
        config = Configuration(host=data['host'], port=data['port'], auth_mode=AuthModeEnum(data['auth_mode']),
                               ssl=data['ssl'], load_from_s3_arn=data['load_from_s3_arn'],
                               aws_region=data['aws_region'], sparql_section=sparql_section,
                               gremlin_section=gremlin_section)
    else:
        config = Configuration(host=data['host'], port=data['port'], ssl=data['ssl'], sparql_section=sparql_section,
                               gremlin_section=gremlin_section)
    return config


def get_config(path: str = DEFAULT_CONFIG_LOCATION) -> Configuration:
    with open(path) as config_file:
        data = json.load(config_file)
        return get_config_from_dict(data)
