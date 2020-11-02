"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os

from jinja2 import Template

dir_path = os.path.dirname(os.path.realpath(__file__))
with open('%s/templates/tabs.html' % dir_path, 'r') as tab_template_file:
    tab_template = tab_template_file.read().strip()
template = Template(tab_template)


class Visualizer(object):
    def __init__(self, query_count=0):
        self.tabs = []
        self.query_count = query_count

    def register_tab(self, tab):
        self.tabs.append(tab)

    def to_html(self):
        tabs = []
        for t in self.tabs:
            tabs.append(t.__dict__)

        # set the first tab as the active one
        if len(tabs) > 0:
            tabs[0]['display_class'] = 'show'

        html = template.render(tabs=tabs)
        return html


class Tab(object):
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.display_class = 'hide'
