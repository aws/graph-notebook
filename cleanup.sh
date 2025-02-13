#!/bin/bash

rm -f src/graph_notebook/widgets/lib/.tsbuildinfo
find . -name ".tsbuildinfo" -delete

rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
rm -rf src/*.egg-info/
rm -rf src/graph_notebook.egg-info/
rm -rf src/graph_notebook/*.egg-info/
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

cd src/graph_notebook/widgets
rm -rf node_modules/
rm -rf lib/
rm -rf dist/
rm -rf labextension/
rm -rf nbextension/
rm -f package-lock.json
cd ../../../

pip cache purge

rm -rf .eggs/
rm -rf .tox/
rm -f MANIFEST

pip uninstall -y jupyterlab jupyterlab-server graph_notebook
pip install jupyterlab==4.2.6

pip install setuptools wheel twine