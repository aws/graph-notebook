"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--notebooks-dir', default='', type=str, help='The directory to start Jupyter from.')

    args = parser.parse_args()

    kernel_manager_option = "--NotebookApp.kernel_manager_class=notebook.services.kernels.kernelmanager.AsyncMappingKernelManager"
    notebooks_dir = '~/notebook/destination/dir' if args.notebooks_dir == '' else args.notebooks_dir

    os.system(f'''jupyter notebook {kernel_manager_option} {notebooks_dir}''')


if __name__ == '__main__':
    main()
