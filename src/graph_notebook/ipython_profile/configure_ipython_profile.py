"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
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


def read_ipython_config():
    try:
        os.makedirs(IPYTHON_DIR_TREE, exist_ok=True)
        with open(IPYTHON_CFG_PATH, 'r') as file:
            ipython_cfg = json.load(file)
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        ipython_cfg = {}

    return ipython_cfg


def write_ipython_config(config):
    with open(IPYTHON_CFG_PATH, 'w') as file:
        json.dump(config, file, indent=2)


def configure_magics_extension():
    ipython_cfg = read_ipython_config()
    try:
        if MAGICS_EXT_NAME not in ipython_cfg["InteractiveShellApp"]["extensions"]:
            ipython_cfg["InteractiveShellApp"]["extensions"].append(MAGICS_EXT_NAME)
    except KeyError:
        ipython_cfg["InteractiveShellApp"] = EXTENSIONS_CFG

    write_ipython_config(ipython_cfg)


if __name__ == '__main__':
    configure_magics_extension()
