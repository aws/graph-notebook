"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import pathlib
import os
import shutil

DEFAULT_NOTEBOOK_DIR = os.getcwd()
EXCLUDED_ITEMS = ['__init__.py', '.ipynb_checkpoints', 'install.py', '__pycache__']
NOTEBOOK_BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def get_all_notebooks_paths(path: str = '') -> list:
    notebooks = []
    if path == '':
        path = NOTEBOOK_BASE_DIR
    items = os.listdir(path)
    for item in items:
        if item in EXCLUDED_ITEMS:
            continue

        full_item_path = f'{path}/{item}'
        if item.endswith('.ipynb'):
            notebooks.append(full_item_path)

        if os.path.isdir(full_item_path):
            notebooks.extend(get_all_notebooks_paths(f'{path}/{item}'))

    return notebooks


def copy_notebooks_to_directory(destination, notebook_path: str = ''):
    """
    copy one or all notebooks to a target directory

    :param destination:     The directory to copy to
    :param notebook_path:   The path from this directory to the target notebook or notebook directory.
                            For example: 01-Getting-Started/01-About-the-Neptune-Notebook.ipynb
    """
    if notebook_path == '':
        notebook_path = NOTEBOOK_BASE_DIR
    items = os.listdir(notebook_path)
    for item in items:
        if item in EXCLUDED_ITEMS:
            continue

        full_item_path = f'{notebook_path}/{item}'
        if os.path.isdir(full_item_path):
            copy_notebooks_to_directory(f'{destination}/{item}', f'{notebook_path}/{item}')
        else:
            copy_path = f'{notebook_path}/{item}'
            if not os.path.exists(destination):
                pathlib.Path(destination).mkdir(parents=True, exist_ok=True)

            print(f'Copying {item} to {destination}')
            shutil.copy2(copy_path, destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=str,
                        help='destination to copy notebooks to. Defaults to current working directory',
                        default=DEFAULT_NOTEBOOK_DIR)
    parser.add_argument('--notebook-path', type=str, default='',
                        help='notebook to copy. If not specified, copy all notebooks')

    args = parser.parse_args()
    copy_notebooks_to_directory(args.destination, args.notebook_path)
