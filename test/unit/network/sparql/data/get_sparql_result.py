"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
import os


dir_path = os.path.dirname(os.path.realpath(__file__))


def get_sparql_result(name):
    file_path = f'{dir_path}/{name}'
    with open(file_path) as f:
        data = json.load(f)
        return data
