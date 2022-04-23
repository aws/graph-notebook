"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import argparse
import json

HOME_PATH = os.path.expanduser("~")
IPYTHON_DIR_TREE = HOME_PATH + '/.ipython/profile_default'
IPYTHON_CFG_FILE_NAME = 'ipython_config.json'
IPYTHON_CFG_PATH = IPYTHON_DIR_TREE + '/' + IPYTHON_CFG_FILE_NAME

MAGICS_EXT_NAME = 'graph_notebook.magics'
EXTENSIONS_CFG = {
    "extensions": [
        MAGICS_EXT_NAME
    ]
}


def configure_ipython_profile():
    try:
        os.makedirs(IPYTHON_DIR_TREE, exist_ok=True)
        with open(IPYTHON_CFG_PATH, 'r') as file:
            ipython_cfg = json.load(file)
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        ipython_cfg = {}

    try:
        if MAGICS_EXT_NAME not in ipython_cfg["InteractiveShellApp"]["extensions"]:
            ipython_cfg["InteractiveShellApp"]["extensions"].append(MAGICS_EXT_NAME)
    except KeyError:
        ipython_cfg["InteractiveShellApp"] = EXTENSIONS_CFG

    with open(IPYTHON_CFG_PATH, 'w') as file:
        json.dump(ipython_cfg, file, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jupyter-dir', default='', type=str, help='The directory to start Jupyter from.')

    args = parser.parse_args()

    configure_ipython_profile()

    jupyter_dir = '~/notebook/destination/dir' if args.jupyter_dir == '' else args.jupyter_dir
    os.system(f'''jupyter lab {jupyter_dir}''')


if __name__ == '__main__':
    main()
