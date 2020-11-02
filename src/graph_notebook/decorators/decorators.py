"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import functools
import json

from IPython.core.display import HTML, display, clear_output

import ipywidgets as widgets
from graph_notebook.visualization.template_retriever import retrieve_template
from gremlin_python.driver.protocol import GremlinServerError
from requests import HTTPError

error_template = retrieve_template("error.html")


def display_exceptions(func):
    @functools.wraps(func)
    def do_display_exceptions(*args, **kwargs):
        clear_output()
        tab = widgets.Tab()
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print('Keyboard interrupt detected.')
            return  # we must return since we have halted the kernel interrupt here. Otherwise the interrupt will not work.
        except HTTPError as http_ex:
            raw_html = http_ex_to_html(http_ex)
        except GremlinServerError as gremlin_ex:
            raw_html = gremlin_server_error_to_html(gremlin_ex)
        except Exception as e:
            raw_html = exception_to_html(e)

        html = HTML(raw_html)
        html_output = widgets.Output(layout={'overflow': 'scroll'})
        with html_output:
            display(html)
        tab.children = [html_output]
        tab.set_title(0, 'Error')
        display(tab)

    return do_display_exceptions


def http_ex_to_html(http_ex: HTTPError):
    try:
        error = json.loads(http_ex.response.content.decode('utf-8'))
        content = json.dumps(error, indent=2)
    except Exception:
        content = {
            'error': http_ex
        }
    error_html = error_template.render(error=content)
    return error_html


def exception_to_html(ex: Exception):
    content = {
        'error': ex
    }
    error_html = error_template.render(error=content)
    return error_html


def gremlin_server_error_to_html(gremlin_ex: GremlinServerError):
    try:
        error = json.loads(gremlin_ex.args[0][5:])  # remove the leading error code.
        content = json.dumps(error, indent=2)
    except Exception:
        content = {
            'error': gremlin_ex
        }
    error_html = error_template.render(error=content)
    return error_html
