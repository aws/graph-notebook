"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import argparse
import json

HOME_PATH = os.path.expanduser("~")
NOTEBOOK_CFG_PATH = HOME_PATH + '/.jupyter/nbconfig/notebook.json'


def patch_cm_cypher_config():
    cypher_cfg = {
        "cm_config": {
            "smartIndent": False,
            "mode": "cypher"
        }
    }

    try:
        with open(NOTEBOOK_CFG_PATH, 'r') as file:
            notebook_cfg = json.load(file)
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        notebook_cfg = {}

    notebook_cfg["CodeCell"] = cypher_cfg

    with open(NOTEBOOK_CFG_PATH, 'w') as file:
        json.dump(notebook_cfg, file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--notebooks-dir', default='', type=str, help='The directory to start Jupyter from.')

    args = parser.parse_args()

    patch_cm_cypher_config()

    kernel_manager_option = "--NotebookApp.kernel_manager_class=notebook.services.kernels.kernelmanager.AsyncMappingKernelManager"
    notebooks_dir = '~/notebook/destination/dir' if args.notebooks_dir == '' else args.notebooks_dir
    os.system(f'''jupyter notebook {kernel_manager_option} {notebooks_dir}''')


if __name__ == '__main__':
    main()
