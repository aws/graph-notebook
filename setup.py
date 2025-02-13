"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
from os.path import join as pjoin
from setuptools import setup, find_packages


print("Current working directory:", os.getcwd())

# Define base paths
WIDGET_DIR = 'src/graph_notebook/widgets'

def make_relative(path):
    """Ensure path is relative and uses forward slashes"""
    if os.path.isabs(path):
        try:
            path = os.path.relpath(path)
        except ValueError:
            raise ValueError(f"Cannot make path relative: {path}")
    return path.replace(os.sep, '/')

def get_data_files():
    files = []
    
    # Lab extension (only package.json and style.js needed)
    lab_files = [
        (WIDGET_DIR + '/labextension/package.json', 'share/jupyter/labextensions/graph_notebook_widgets'),
        (WIDGET_DIR + '/labextension/static/style.js', 'share/jupyter/labextensions/graph_notebook_widgets/static'),
    ]
    
    # Notebook extension (needs both JS files)
    nb_files = [
        (WIDGET_DIR + '/nbextension/extension.js', 'share/jupyter/nbextensions/graph_notebook_widgets'),
        (WIDGET_DIR + '/nbextension/index.js', 'share/jupyter/nbextensions/graph_notebook_widgets'),
        (WIDGET_DIR + '/graph_notebook_widgets.json', 'etc/jupyter/nbconfig/notebook.d'),
    ]
    
    # Group files by destination
    grouped_files = {}
    for src, dest in lab_files + nb_files:
        src = make_relative(src)
        if os.path.exists(src):  # Only add files that exist
            if dest not in grouped_files:
                grouped_files[dest] = []
            grouped_files[dest].append(src)
            print(f"Adding file: {src} -> {dest}")
        else:
            print(f"Warning: File does not exist: {src}")
    
    # Convert to data_files format
    return [(k, v) for k, v in grouped_files.items()]

data_files = get_data_files()


package_data={
    'graph_notebook': [
        'widgets/nbextension/**/*',
        'widgets/labextension/**/*',
        'widgets/labextension/static/**/*'
    ],
    '': ['*.ipynb', '*.html', '*.css', '*.js', '*.txt', '*.json', '*.ts', '*.yaml', '*.md', '*.tgz']
}


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
    data_files=data_files,
    include_package_data=True,
    install_requires=[
        'gremlinpython>=3.5.1,<=3.7.2',
        'SPARQLWrapper==2.0.0',
        'requests>=2.32.0,<=2.32.2',
        'ipywidgets>=8.0.0,<9.0.0',
        'jupyterlab==4.2.6',
        'jupyterlab_widgets>=3.0.0',
        'networkx==2.4',
        'Jinja2>=3.0.3,<=3.1.4',
        'notebook>=6.1.5,<7.0.0',
        'nbclient<=0.7.3',
        'jupyter-contrib-nbextensions<=0.7.0',
        'botocore>=1.34.74',
        'boto3>=1.34.74',
        'ipython>=7.16.1,<=8.10.0',
        'neo4j>=5.0.0,<=5.23.1',
        'rdflib==7.0.0',
        'ipykernel>=6.5.0',
        'ipyfilechooser==0.6.0',
        'nbconvert>=6.3.0,<=7.2.8',
        'jedi>=0.18.1,<=0.18.2',
        'itables>=2.0.0,<=2.1.0',
        'pandas>=2.1.0,<=2.2.2',
        'numpy<1.24.0',
        'nest_asyncio>=1.5.5,<=1.6.0',
        'async-timeout>=4.0,<5.0',
        'json-repair==0.29.2'
    ],
    package_data=package_data,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: Apache Software License'
    ],
    keywords='jupyter neptune gremlin sparql',
    extras_require={
        'test': [
            'pytest==6.2.5'
            ],
    },
    zip_safe=False,
    python_requires=">=3.8"
)
