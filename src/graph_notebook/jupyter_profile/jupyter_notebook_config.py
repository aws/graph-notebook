"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os

static_path = os.path.expanduser('~/neptune_workbench/static/')
c.NotebookApp.extra_static_paths = [static_path]  # noqa: F821
