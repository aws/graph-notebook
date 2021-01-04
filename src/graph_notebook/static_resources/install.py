"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import site
from shutil import copy2
from os.path import join as pjoin

files = [
    'datatables.css',
    'datatables.js'
]


def main():
    sitepackages = site.getsitepackages()
    static_base_directory = sitepackages[0] if os.name != 'nt' else sitepackages[1]
    destination = pjoin(static_base_directory, 'notebook', 'static')

    dir_path = os.path.dirname(os.path.realpath(__file__))
    for file in files:
        full_path = pjoin(dir_path, file)
        print(f'copying file {file} to {destination}')
        copy2(full_path, destination)


if __name__ == '__main__':
    main()
