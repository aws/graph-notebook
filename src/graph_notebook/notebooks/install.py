"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import pathlib
import os
import shutil
import nbformat

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

def normalize_notebook(file_path: str):
    """
    Process and normalize Jupyter notebooks by:
    1. Removing cell IDs from all cells (these are auto-generated and can cause merge conflicts)
    2. Setting execution_count to None for code cells that don't have it defined
    3. Validating notebook format before and after modifications
    4. Saving changes back to the original file
    
    Args:
        file_path (str): Path to the .ipynb file to normalize
    
    Note: Only processes files with .ipynb extension. Skips malformed notebooks.
    """
    try:
        if not file_path.endswith('.ipynb'):
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                notebook = nbformat.read(f, as_version=4)
            except Exception as e:
                print(f"Notebook does not appear to be JSON: {str(e)}")
                return

        # Validate notebook structure
        if not hasattr(notebook, 'cells') or not isinstance(notebook.cells, list):
            print(f"Skipping malformed notebook: {file_path}")
            return

        # Process cells
        for cell in notebook.cells:
            if 'id' in cell:
                del cell['id']

            if cell.cell_type == 'code' and ('execution_count' not in cell or cell.execution_count is None):
                cell['execution_count'] = None

        # Validate again
        try:
            nbformat.validate(notebook)
        except Exception as e:
            print(f"Validation error for {file_path}: {str(e)}")
            return

        # Save back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            nbformat.write(notebook, f)

    except Exception as e:
        print(f"Error normalizing notebook {file_path}: {str(e)}")


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

        full_item_path = os.path.join(notebook_path, item)
        if os.path.isdir(full_item_path):
            new_destination = os.path.join(destination, item)
            copy_notebooks_to_directory(new_destination, full_item_path)
        else:
            if not os.path.exists(destination):
                pathlib.Path(destination).mkdir(parents=True, exist_ok=True)

            try:
                # Only normalize .ipynb files
                if item.endswith('.ipynb'):
                    normalize_notebook(full_item_path)
                
                print(f'Copying {item} to {destination}')
                shutil.copy2(full_item_path, destination)
            except Exception as e:
                print(f"Error copying {item}: {str(e)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=str,
                        help='destination to copy notebooks to. Defaults to current working directory',
                        default=DEFAULT_NOTEBOOK_DIR)
    parser.add_argument('--notebook-path', type=str, default='',
                        help='notebook to copy. If not specified, copy all notebooks')

    args = parser.parse_args()
    copy_notebooks_to_directory(args.destination, args.notebook_path)
