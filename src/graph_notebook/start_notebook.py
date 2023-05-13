"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import argparse
import json

HOME_PATH = os.path.expanduser("~")
NBCONFIG_DIR_TREE = HOME_PATH + '/.jupyter/nbconfig'
NOTEBOOK_CFG_PATH = NBCONFIG_DIR_TREE + '/notebook.json'

CUSTOM_DIR_TREE = HOME_PATH + '/.jupyter/custom'
NOTEBOOK_CUSTOMJS_PATH = CUSTOM_DIR_TREE + '/custom.js'


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


def patch_customjs():
    # Increases time allotted to load nbextensions on large notebooks. Limit is set to 60s and can be increased further.
    # Reference: https://github.com/ipython-contrib/jupyter_contrib_nbextensions/blob/master/docs/source/troubleshooting.md#extensions-not-loading-for-large-notebooks
    limit = "60"
    increase_requirejs_timeout_prefix = "window.requirejs.config({waitSeconds:"
    increase_requirejs_timeout_suffix = "});"
    requirejs_timeout_full = increase_requirejs_timeout_prefix + limit + increase_requirejs_timeout_suffix

    try:
        os.makedirs(CUSTOM_DIR_TREE, exist_ok=True)
        with open(NOTEBOOK_CUSTOMJS_PATH, 'r') as file:
            customjs_content = file.read()
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        customjs_content = ""

    if increase_requirejs_timeout_prefix not in customjs_content:
        if customjs_content:
            customjs_content += "\n"
        customjs_content += requirejs_timeout_full
        with open(NOTEBOOK_CUSTOMJS_PATH, 'w') as file:
            file.write(customjs_content)
        print(f"Modified nbextensions loader timeout limit to {limit} seconds")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--notebooks-dir', default='', type=str, help='The directory to start Jupyter from.')

    args = parser.parse_args()

    patch_cm_cypher_config()
    patch_customjs()

    kernel_manager_option = "--NotebookApp.kernel_manager_class=notebook.services.kernels.kernelmanager.AsyncMappingKernelManager"
    notebooks_dir = '~/notebook/destination/dir' if args.notebooks_dir == '' else args.notebooks_dir
    os.system(f'''jupyter notebook {kernel_manager_option} {notebooks_dir}''')


if __name__ == '__main__':
    main()
