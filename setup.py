"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import site

from os.path import join as pjoin
from setuptools import setup, find_packages
from setupbase import (
    create_cmdclass, install_npm, ensure_targets,
    combine_commands, HERE, widgets_root
)

nb_path = pjoin(HERE, 'src', 'graph_notebook', 'widgets', 'nbextension', 'static')
lab_path = pjoin(HERE, 'src', 'graph_notebook', 'widgets', 'labextension')

js_targets = [
    pjoin(nb_path, 'index.js'),
    pjoin(HERE, 'src', 'graph_notebook', 'widgets', 'lib', 'plugin.d.ts')
]

package_data_spec = {
    'graph_notebook_widgets': [
        'nbextension/static/*.*js*',
        'labextension/*.tgz'
    ]
}

data_files_spec = [
    ('share/jupyter/nbextensions/graph_notebook_widgets',
     nb_path, '*.js*'),
    ('share/jupyter/lab/extensions', lab_path, '*.tgz'),
    ('etc/jupyter/nbconfig/notebook.d', HERE, 'graph_notebook_widgets.json')
]

cmd_class = create_cmdclass('jsdeps', package_data_spec=package_data_spec, data_files_spec=data_files_spec)
cmd_class['jsdeps'] = combine_commands(
    install_npm(widgets_root, build_cmd='build:all'),
    ensure_targets(js_targets),
)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="graph-notebook",
    author='amazon-neptune',
    author_email="graph-notebook@amazon.com",
    description="jupyter notebook extension to connect to graph databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aws/graph-notebook",
    version="1.05",
    packages=find_packages(where="src", exclude=("test",)),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        'gremlinpython==3.4.3',
        'SPARQLWrapper==1.8.4',
        'tornado==4.5.3',
        'requests',
        'ipywidgets<=7.5.1',
        'networkx==2.4',
        'Jinja2==2.10.1',
        'notebook<=5.7.8',
    ],
    package_data={
        '': ['*.ipynb', '*.html', '*.css', '*.js', '*.txt', '*.json', '*.ts', '*.css', '*.yaml', '*.mdinstall_npm', '*.tgz']
    },
    cmdclass=cmd_class
)
