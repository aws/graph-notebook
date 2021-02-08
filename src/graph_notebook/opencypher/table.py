"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""


def get_rows_and_columns(oc_results):
    if type(oc_results) is not dict:
        return None

    if 'head' in oc_results and 'vars' in oc_results['head'] and 'results' in oc_results and 'bindings' in \
            oc_results['results']:
        columns = []
        for v in oc_results['head']['vars']:
            columns.append(v)

        rows = []
        for binding in oc_results['results']['bindings']:
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
