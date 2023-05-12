"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import functools
import json
import re
import traceback

from IPython.core.display import HTML, display, clear_output

import ipywidgets as widgets
from graph_notebook.visualization.template_retriever import retrieve_template
from gremlin_python.driver.protocol import GremlinServerError
from requests import HTTPError

error_template = retrieve_template("error.html")

check_if_access_regex = re.compile(r'^[a-zA-Z0-9_]+((\[\'.*?\'\])|(\[\".*?\"\])|(\[.*?\]))+$')
var_name_regex = re.compile(r'^[^\[]*')


def get_variable_injection_name_and_indices(raw_var: str, keys_are_str: bool = True):
    # get the name of the dict
    var_name = var_name_regex.match(raw_var).group(0)
    # get the rest of the string, containing all the nested keys
    keys_raw = raw_var[len(var_name):len(raw_var)]
    # remove all quotes before we split to keys
    keys_raw = keys_raw.replace('"', "").replace("'", "")
    keys_list = keys_raw[1:(len(keys_raw) - 1)].split("][")

    if not keys_are_str:
        keys_list = [int(x) for x in keys_raw[1:(len(keys_raw) - 1)].split("][")]

    return var_name, keys_list


def get_variable_injection_value(raw_var: str, local_ns: dict):
    # check if var string is trying to access a dict
    if re.match(check_if_access_regex, raw_var):
        var_name, keys_list = get_variable_injection_name_and_indices(raw_var)
        # outer try/except statement in use_magic_variable should catch case where dict_name isn't in local_ns
        current_value = local_ns[var_name]
        # loop through the nested keys/values until we get the final value
        for key in keys_list:
            if isinstance(current_value, dict):
                current_value = current_value[key]
            else:  # for list/tuple, try to convert to int first
                try:
                    index_key = int(key)
                except ValueError:
                    print("Error occurred during variable injection: Attempted to access tuple/list with str index. "
                          "Please check your query.")
                    return
                current_value = current_value[index_key]
        final_value = json.dumps(current_value) if type(current_value) is dict else str(current_value)
        return final_value
    else:
        final_value = local_ns[raw_var]
        if type(final_value) is dict:
            return json.dumps(final_value)
        else:
            return str(final_value)


def display_exceptions(func):
    @functools.wraps(func)
    def do_display_exceptions(*args, **kwargs):
        try:
            show_traceback = kwargs['local_ns']['graph_notebook_show_traceback']
        except KeyError:
            show_traceback = False
        clear_output()
        tab = widgets.Tab()

        server_error = False
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print('Keyboard interrupt detected.')
            return  # we must return since we have halted the kernel interrupt here. Otherwise the interrupt will not work.
        except HTTPError as http_ex:
            caught_ex = http_ex
            raw_html = http_ex_to_html(http_ex)
            server_error = True
        except GremlinServerError as gremlin_ex:
            caught_ex = gremlin_ex
            raw_html = gremlin_server_error_to_html(gremlin_ex)
            server_error = True
        except Exception as e:
            if show_traceback:
                caught_ex = traceback.format_exception(e)
                traceback.print_exception(e)
            else:
                caught_ex = e
                raw_html = exception_to_html(e)

        if 'local_ns' in kwargs:
            kwargs['local_ns']['graph_notebook_error'] = caught_ex

        if server_error or not show_traceback:
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
                args[2] = variable_regex.sub(
                    lambda m: get_variable_injection_value(raw_var=m.group(1), local_ns=local_ns), cell_string)
            return func(*args, **kwargs)
        except KeyError as key_error:
            print(f'Terminated magic due to undefined variable: {key_error}')
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


def exception_to_html(ex):
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
