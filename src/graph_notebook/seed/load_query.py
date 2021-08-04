"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
from os.path import join as pjoin


def normalize_model_name(name):
    name = name.lower().replace('_', '')
    # handles legacy scenarios
    if name=='gremlin':
        name='propertygraph'
    elif name=='sparql':
        name='rdf' 
    return name


# returns a list of queries which correspond to a given query language and name
def get_queries(model, name):
    d = os.path.dirname(os.path.realpath(__file__))
    path_to_data_sets = pjoin(d, 'queries', normalize_model_name(model), name)
    queries = []

    for file in os.listdir(path_to_data_sets):
        if file == '__init__.py' or file == '__pycache__':
            continue
        full_path = pjoin(path_to_data_sets, file)
        with open(full_path, mode='r', encoding="utf-8") as f:
            query = {
                'name': file,
                'content': f.read()
            }
            queries.append(query)
    queries.sort(key=lambda i: i['name'])  # ensure we get queries back in lexographical order.
    return queries


def get_data_sets(model):
    if model == '':
      return []
    d = os.path.dirname(os.path.realpath(__file__))
    path_to_data_sets = pjoin(d, 'queries', normalize_model_name(model))
    data_sets = []
    for data_set in os.listdir(path_to_data_sets):
        if data_set != '__pycache__' and os.path.isdir(pjoin(path_to_data_sets, data_set)):
            data_sets.append(data_set)
    return data_sets
