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

nb_path = pjoin(widgets_root, 'nbextension')
lab_path = pjoin(widgets_root, 'labextension')

js_targets = [
    pjoin(nb_path, 'index.js'),
    pjoin(lab_path, 'package.json')
]

package_data_spec = {
    'graph_notebook_widgets': [
        'nbextension/**js*',
        'labextension/**'
    ]
}

data_files_spec = [
    ('share/jupyter/nbextensions/graph_notebook_widgets', nb_path, '**'),
    ('share/jupyter/labextensions/graph_notebook_widgets', lab_path, '**'),
    ('share/jupyter/labextensions/graph_notebook_widgets', HERE, 'install.json'),
    ('etc/jupyter/nbconfig/notebook.d', HERE, 'graph_notebook_widgets.json')
]

cmd_class = create_cmdclass('jsdeps', package_data_spec=package_data_spec, data_files_spec=data_files_spec)
cmd_class['jsdeps'] = combine_commands(
    install_npm(widgets_root, build_cmd='build:prod'),
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
        'gremlinpython>=3.5.1',
        'SPARQLWrapper==1.8.4',
        'requests',
        'ipywidgets==7.7.2',
        'jupyterlab_widgets>=1.0.0,<3.0.0',
        'networkx==2.4',
        'Jinja2==3.0.3',
        'notebook>=6.1.5,<6.5.0',
        'nbclient<=0.7.0',
        'jupyter-contrib-nbextensions',
        'widgetsnbextension',
        'jupyter>=1.0.0',
        'botocore>=1.19.37',
        'boto3>=1.17.58',
        'ipython>=7.16.1,<7.17.0',
        'neo4j==4.3.2',
        'rdflib==5.0.0',
        'ipykernel==5.3.4',
        'nbconvert>=6.3.0',
        'jedi<0.18.0',
        'markupsafe<2.1.0',
        'itables>=1.0.0',
        'pandas'
    ],
    package_data={
        'graph_notebook': ['graph_notebook/widgets/nbextensions/**',
                           'graph_notebook/widgets/labextension/**'],
        '': ['*.ipynb', '*.html', '*.css', '*.js', '*.txt', '*.json', '*.ts', '*.css', '*.yaml', '*.md', '*.tgz']
    },
    cmdclass=cmd_class,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Apache Software License'
    ],
    keywords='jupyter neptune gremlin sparql',
    tests_require=[
        'pytest'
    ]
)
