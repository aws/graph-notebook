"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""


# template for this taken from
# https://jupyter-notebook.readthedocs.io/en/stable/examples/Notebook/Distributing%20Jupyter%20Extensions%20as%20Python%20Packages.html#Defining-the-server-extension-and-nbextension
def _jupyter_nbextension_paths():
    return [dict(
        section="notebook",
        src="static",
        dest="sparql_syntax",
        require="sparql_syntax/main")]
