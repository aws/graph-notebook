"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import shutil
import argparse
from pathlib import Path
from graph_notebook.ipython_profile.configure_ipython_profile import configure_magics_extension


def install_custom_css():
    config_dir = Path(os.environ.get('JUPYTER_CONFIG_DIR', os.path.expanduser('~/.jupyter')))
    dest = config_dir / 'custom'
    dest.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).parent / 'jupyter_profile' / 'custom' / 'custom.css'
    shutil.copy2(src, dest / 'custom.css')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jupyter-dir', default='', type=str, help='The directory to start Jupyter from.')

    args = parser.parse_args()

    configure_magics_extension()
    install_custom_css()

    jupyter_dir = '~/notebook/destination/dir' if args.jupyter_dir == '' else args.jupyter_dir
    os.system(f'''jupyter lab --custom-css {jupyter_dir}''')


if __name__ == '__main__':
    main()
