"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import functools
import json
import re

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
            caught_ex = http_ex
            raw_html = http_ex_to_html(http_ex)
        except GremlinServerError as gremlin_ex:
            caught_ex = gremlin_ex
            raw_html = gremlin_server_error_to_html(gremlin_ex)
        except Exception as e:
            caught_ex = e
            raw_html = exception_to_html(e)

        if 'local_ns' in kwargs:
            kwargs['local_ns']['graph_notebook_error'] = caught_ex

        html = HTML(raw_html)
        html_output = widgets.Output(layout={'overflow': 'scroll'})
        with html_output:
            display(html)
        tab.children = [html_output]
        tab.set_title(0, 'Error')
        display(tab)

    return do_display_exceptions


def magic_variables(func):
    @functools.wraps(func)
    def use_magic_variables(*args, **kwargs):
        local_ns = kwargs['local_ns']
        args = list(args)
        variable_regex = re.compile(r'\$\{(.*?)}')
        try:
            # If we want to use custom line magic variables with the same syntax:
            # line_string = args[1]
            # args[1] = variable_regex.sub(lambda m: str(local_ns[m.group(1)]), line_string)
            if len(args) > 2:
                cell_string = args[2]
                args[2] = variable_regex.sub(lambda m: json.dumps(local_ns[m.group(1)]) if type(local_ns[m.group(1)]) is dict else str(local_ns[m.group(1)]), cell_string)
            return func(*args, **kwargs)
        except KeyError as key_error:
            print(f'Terminated query due to undefined variable: {key_error}')
            return

    return use_magic_variables


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
