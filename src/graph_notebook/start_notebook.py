"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import argparse
import json

HOME_PATH = os.path.expanduser("~")
NBCONFIG_DIR_TREE = HOME_PATH + '/.jupyter/nbconfig'
CFG_FILE_NAME = 'notebook.json'
NOTEBOOK_CFG_PATH = NBCONFIG_DIR_TREE + '/' + CFG_FILE_NAME

def patch_cm_cypher_config():
    cypher_cfg = {
        "cm_config": {
            "smartIndent": False
        }
    }

    try:
        os.makedirs(NBCONFIG_DIR_TREE, exist_ok=True)
        with open(NOTEBOOK_CFG_PATH, 'r') as file:
            notebook_cfg = json.load(file)
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        notebook_cfg = {}

    notebook_cfg["CodeCell"] = cypher_cfg

    with open(NOTEBOOK_CFG_PATH, 'w') as file:
        json.dump(notebook_cfg, file, indent=2)


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
