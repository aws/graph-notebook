"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

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


def get_version():
    with open('src/graph_notebook/__init__.py') as f:
        for line in f:
            if line.startswith('__version__'):
                _, _, version = line.replace("'", '').split()
                break
    if version == '':
        raise ValueError('no version found')
    return version


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='graph-notebook',
    author='amazon-neptune',
    author_email='amazon-neptune-pypi@amazon.com',
    description='jupyter notebook extension to connect to graph databases',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/aws/graph-notebook',
    version=get_version(),
    packages=find_packages(where='src', exclude=('test',)),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'gremlinpython',
        'SPARQLWrapper==1.8.4',
        'tornado==4.5.3',
        'requests',
        'ipywidgets',
        'networkx==2.4',
        'Jinja2==2.10.1',
        'notebook',
        'jupyter-contrib-nbextensions',
        'widgetsnbextension',
        'jupyter>=1.0.0'
    ],
    package_data={
        'graph_notebook': ['graph_notebook/widgets/nbextensions/static/*.js',
                           'graph_notebook/widgets/labextension/*.tgz'],
        '': ['*.ipynb', '*.html', '*.css', '*.js', '*.txt', '*.json', '*.ts', '*.css', '*.yaml', '*.md', '*.tgz']
    },
    cmdclass=cmd_class,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License'
    ],
    keywords='jupyter neptune gremlin sparql',
)
