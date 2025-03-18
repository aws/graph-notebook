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

    # JupyterLab 4 and Notebook 7+ use a different extension system with Prebuilt extensions instead of nbextensions
    # Therefore, we need to install as a labextension for modern environments
    # NOTE: Our custom extension plugins defined here will not work in notebook 7+ yet
    os.system(f'jupyter labextension install {plugin_name}')

    # For classic notebook features, We still need nbclassic for traditional nbextension support
    if os.system('jupyter nbclassic --version') == 0:  # Check if nbclassic is available
        os.system(f'jupyter nbclassic-extension install --py {plugin_name} --sys-prefix')
        os.system(f'jupyter nbclassic-extension enable --py {plugin_name} --sys-prefix')

if __name__ == '__main__':
    main()