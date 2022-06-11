"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import argparse
from graph_notebook.ipython_profile.configure_ipython_profile import configure_magics_extension


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jupyter-dir', default='', type=str, help='The directory to start Jupyter from.')

    args = parser.parse_args()

    configure_magics_extension()

    jupyter_dir = '~/notebook/destination/dir' if args.jupyter_dir == '' else args.jupyter_dir
    os.system(f'''jupyter lab {jupyter_dir}''')


if __name__ == '__main__':
    main()
