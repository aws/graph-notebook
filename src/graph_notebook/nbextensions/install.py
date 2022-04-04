"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import os

PLUGINS = [
    'neptune_menu',
    'gremlin_syntax',
    'sparql_syntax',
    'opencypher_syntax',
    'playable_cells'
]

dir_path = os.path.dirname(os.path.realpath(__file__))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plugin-name', default='', type=str, help='install and enable this jupyter plugin')

    args = parser.parse_args()
    plugin_name = 'graph_notebook.nbextensions' if args.plugin_name == '' else args.plugin_name
    os.system(f'''jupyter nbextension install --py {plugin_name} --sys-prefix --overwrite''')
    os.system(f'''jupyter nbextension enable --py {plugin_name} --sys-prefix''')


if __name__ == '__main__':
    main()