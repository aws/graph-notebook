"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os


def main():

    kernel_manager_option = "--NotebookApp.kernel_manager_class=notebook.services.kernels.kernelmanager.AsyncMappingKernelManager"

    os.system(f'''jupyter notebook {kernel_manager_option} ~/notebook/destination/dir''')


if __name__ == '__main__':
    main()
