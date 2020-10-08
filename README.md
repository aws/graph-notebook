## graph-notebook

Python package integrating jupyter notebooks with various graph-stores including
[Apache Tinkerpop](https://tinkerpop.apache.org/) and [RDF SPARQL](https://www.w3.org/TR/rdf-sparql-query/).

## Requirements
- Python3.6
- Jupyter Notebooks

## Installation

```
# install the package
pip install graph-notebook

# install and enable the visualization widget
jupyter nbextension install --py --sys-prefix graph_notebook.widgets
jupyter nbextension enable  --py --sys-prefix graph_notebook.widgets

# copy static html resources
python -m graph_notebook.static_resources.install
python -m graph_notebook.nbextensions.install

# copy premade starter notebooks
python -m graph_notebook.notebooks.install --destination /notebook/destination/dir  
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

