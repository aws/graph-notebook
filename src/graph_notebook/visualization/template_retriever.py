"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os

from jinja2.sandbox import SandboxedEnvironment

dir_path = os.path.dirname(os.path.realpath(__file__))


def retrieve_template(template_name):
    with open('%s/templates/%s' % (dir_path, template_name), 'r') as tab_template_file:
        tab_template = tab_template_file.read().strip()

    env = SandboxedEnvironment()
    template = env.from_string(tab_template)

    return template
