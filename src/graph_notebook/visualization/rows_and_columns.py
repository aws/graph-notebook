"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
from itertools import chain
from collections import OrderedDict


def sparql_get_rows_and_columns(sparql_results):
    if type(sparql_results) is not dict:
        return None

    if 'head' in sparql_results and 'vars' in sparql_results['head'] and 'results' in sparql_results and 'bindings' in \
            sparql_results['results']:
        columns = []
        for v in sparql_results['head']['vars']:
            columns.append(v)

        rows = []
        for binding in sparql_results['results']['bindings']:
            row = []
            for c in columns:
                if c in binding:
                    row.append(binding[c]['value'])
                else:
                    row.append('-')  # handle non-existent bindings for optional variables.
            rows.append(row)

        return {
            'columns': columns,
            'rows': rows
        }
    else:
        return None

def opencypher_get_rows_and_columns(results, is_bolt=False):
    rows = []
    columns = set()

    if not is_bolt:
        if results['results']:
            res=results['results']
        else:
            return None
    else:
        res=results
    
    if len(res)>0:
        columns=res[0].keys()
    
    for r in res:
        row = []
        for key, item in r.items():
            row.append(item)
        rows.append(row)

    return {
        'columns': columns,
        'rows': rows
    }

