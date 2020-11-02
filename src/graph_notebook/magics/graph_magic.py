"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from __future__ import print_function  # Python 2/3 compatibility

import argparse
import logging
import json
import time
import os
import uuid
from enum import Enum

import ipywidgets as widgets
from gremlin_python.driver.protocol import GremlinServerError
from IPython.core.display import HTML, display_html, display
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic, line_cell_magic)
from ipywidgets.widgets.widget_description import DescriptionStyle
from requests import HTTPError

import graph_notebook
from graph_notebook.configuration.generate_config import generate_default_config
from graph_notebook.decorators.decorators import display_exceptions
from graph_notebook.network import SPARQLNetwork
from graph_notebook.network.gremlin.GremlinNetwork import parse_pattern_list_str, GremlinNetwork
from graph_notebook.sparql.table import get_rows_and_columns
from graph_notebook.gremlin.query import do_gremlin_query, do_gremlin_explain, do_gremlin_profile
from graph_notebook.gremlin.status import do_gremlin_status, do_gremlin_cancel
from graph_notebook.sparql.query import get_query_type, do_sparql_query, do_sparql_explain
from graph_notebook.sparql.status import do_sparql_status, do_sparql_cancel
from graph_notebook.system.database_reset import perform_database_reset, initiate_database_reset
from graph_notebook.visualization.template_retriever import retrieve_template
from graph_notebook.gremlin.client_provider.factory import create_client_provider
from graph_notebook.request_param_generator.sparql_request_generator import SPARQLRequestGenerator
from graph_notebook.request_param_generator.factory import create_request_generator
from graph_notebook.loader.load import do_load, get_loader_jobs, get_load_status, cancel_load
from graph_notebook.configuration.get_config import get_config, get_config_from_dict
from graph_notebook.seed.load_query import get_data_sets, get_queries
from graph_notebook.status.get_status import get_status
from graph_notebook.widgets import Force
from graph_notebook.options import OPTIONS_DEFAULT_DIRECTED, vis_options_merge

sparql_table_template = retrieve_template("sparql_table.html")
sparql_explain_template = retrieve_template("sparql_explain.html")
sparql_construct_template = retrieve_template("sparql_construct.html")
gremlin_table_template = retrieve_template("gremlin_table.html")
pre_container_template = retrieve_template("pre_container.html")
loading_wheel_template = retrieve_template("loading_wheel.html")
error_template = retrieve_template("error.html")

loading_wheel_html = loading_wheel_template.render()
DEFAULT_LAYOUT = widgets.Layout(max_height='600px', overflow='scroll', width='100%')

logging.basicConfig()
logger = logging.getLogger("graph_magic")

DEFAULT_MAX_RESULTS = 1000

GREMLIN_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery, for example: %gremlin_status --cancelQuery --queryId my-query-id'''
SPARQL_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery, for example: %sparql_status --cancelQuery --queryId my-query-id'''
SEED_LANGUAGE_OPTIONS = ['', 'Gremlin', 'SPARQL']


class QueryMode(Enum):
    DEFAULT = 'query'
    EXPLAIN = 'explain'
    PROFILE = 'profile'
    EMPTY = ''


def str_to_query_mode(s: str) -> QueryMode:
    s = s.lower()
    for mode in list(QueryMode):
        if mode.value == s:
            return QueryMode(s)

    logger.debug(f'Invalid query mode {s} supplied, defaulting to query.')
    return QueryMode.DEFAULT


@magics_class
class Graph(Magics):
    def __init__(self, shell):
        # You must call the parent constructor
        super(Graph, self).__init__(shell)

        try:
            self.graph_notebook_config = get_config()
        except FileNotFoundError:
            self.graph_notebook_config = generate_default_config()
            print('Could not find a valid configuration. Do not forgot to validate your settings using %graph_notebook_config')
        self.max_results = DEFAULT_MAX_RESULTS
        self.mode = QueryMode.DEFAULT
        self.graph_notebook_vis_options = OPTIONS_DEFAULT_DIRECTED
        logger.setLevel(logging.ERROR)

    @line_cell_magic
    @display_exceptions
    def graph_notebook_config(self, line='', cell=''):
        if cell != '':
            data = json.loads(cell)
            config = get_config_from_dict(data)
            self.graph_notebook_config = config
        elif line == 'reset':
            self.graph_notebook_config = get_config()
            print('reset notebook config to:')
            print(json.dumps(self.graph_notebook_config.to_dict(), indent=2))
        else:
            config_dict = self.graph_notebook_config.to_dict()
            return print(json.dumps(config_dict, indent=2))

    @line_magic
    def graph_notebook_host(self, line):
        if line == '':
            print('please specify a host.')
            return

        # TODO: we should attempt to make a status call to this host before we set the config to this value.
        self.graph_notebook_config.host = line
        print(f'set host to {line}')

    @cell_magic
    @display_exceptions
    def sparql(self, line='', cell=''):
        request_generator = create_request_generator(self.graph_notebook_config.auth_mode,
                                                     self.graph_notebook_config.iam_credentials_provider_type,
                                                     command='sparql')

        if line != '':
            mode = str_to_query_mode(line)
        else:
            mode = self.mode
        tab = widgets.Tab()
        logger.debug(f'using mode={mode}')
        if mode == QueryMode.EXPLAIN:
            html_raw = sparql_explain(cell, self.graph_notebook_config.host, self.graph_notebook_config.port,
                                      self.graph_notebook_config.ssl, request_generator)
            explain_output = widgets.Output(layout=DEFAULT_LAYOUT)
            with explain_output:
                display(HTML(html_raw))

            tab.children = [explain_output]
            tab.set_title(0, 'Explain')
            display(tab)
        else:
            query_type = get_query_type(cell)
            headers = {} if query_type not in ['SELECT', 'CONSTRUCT', 'DESCRIBE'] else {
                'Accept': 'application/sparql-results+json'}
            res = do_sparql_query(cell, self.graph_notebook_config.host, self.graph_notebook_config.port,
                                  self.graph_notebook_config.ssl, request_generator, headers)
            titles = []
            children = []

            display(tab)
            table_output = widgets.Output(layout=DEFAULT_LAYOUT)
            # Assign an empty value so we can always display to table output.
            # We will only add it as a tab if the type of query allows it.
            # Because of this, the table_output will only be displayed on the DOM if the query was of type SELECT.
            table_html = ""
            query_type = get_query_type(cell)
            if query_type in ['SELECT', 'CONSTRUCT', 'DESCRIBE']:
                logger.debug('creating sparql network...')

                # some issues with displaying a datatable when not wrapped in an hbox and displayed last
                hbox = widgets.HBox([table_output], layout=DEFAULT_LAYOUT)
                titles.append('Table')
                children.append(hbox)

                expand_all = line == '--expand-all'
                sn = SPARQLNetwork(expand_all=expand_all)
                sn.extract_prefix_declarations_from_query(cell)
                try:
                    sn.add_results(res)
                except ValueError as value_error:
                    logger.debug(value_error)

                logger.debug(f'number of nodes is {len(sn.graph.nodes)}')
                if len(sn.graph.nodes) > 0:
                    f = Force(network=sn, options=self.graph_notebook_vis_options)
                    titles.append('Graph')
                    children.append(f)
                    logger.debug('added sparql network to tabs')

                rows_and_columns = get_rows_and_columns(res)
                if rows_and_columns is not None:
                    table_id = f"table-{str(uuid.uuid4())[:8]}"
                    table_html = sparql_table_template.render(columns=rows_and_columns['columns'],
                                                              rows=rows_and_columns['rows'], guid=table_id)

                # Handling CONSTRUCT and DESCRIBE on their own because we want to maintain the previous result pattern
                # of showing a tsv with each line being a result binding in addition to new ones.
                if query_type == 'CONSTRUCT' or query_type == 'DESCRIBE':
                    lines = []
                    for b in res['results']['bindings']:
                        lines.append(f'{b["subject"]["value"]}\t{b["predicate"]["value"]}\t{b["object"]["value"]}')
                    raw_output = widgets.Output(layout=DEFAULT_LAYOUT)
                    with raw_output:
                        html = sparql_construct_template.render(lines=lines)
                        display(HTML(html))
                    children.append(raw_output)
                    titles.append('Raw')

            json_output = widgets.Output(layout=DEFAULT_LAYOUT)
            with json_output:
                print(json.dumps(res, indent=2))
            children.append(json_output)
            titles.append('JSON')

            tab.children = children
            for i in range(len(titles)):
                tab.set_title(i, titles[i])

            with table_output:
                display(HTML(table_html))

    @line_magic
    @display_exceptions
    def sparql_status(self, line=''):
        parser = argparse.ArgumentParser()
        parser.add_argument('-q', '--queryId', default='',
                            help='The ID of a running SPARQL query. Only displays the status of the specified query.')
        parser.add_argument('-c', '--cancelQuery', action='store_true',
                            help='Tells the status command to cancel a query. This parameter does not take a value')
        parser.add_argument('-s', '--silent', action='store_true',
                            help='If silent=true then the running query is cancelled and the HTTP response code is 200. If silent is not present or silent=false, the query is cancelled with an HTTP 500 status code.')
        args = parser.parse_args(line.split())

        request_generator = create_request_generator(self.graph_notebook_config.auth_mode,
                                                     self.graph_notebook_config.iam_credentials_provider_type)

        if not args.cancelQuery:
            res = do_sparql_status(self.graph_notebook_config.host, self.graph_notebook_config.port,
                                   self.graph_notebook_config.ssl, request_generator, args.queryId)

        else:
            if args.queryId == '':
                print(SPARQL_CANCEL_HINT_MSG)
                return
            else:
                res = do_sparql_cancel(self.graph_notebook_config.host, self.graph_notebook_config.port,
                                       self.graph_notebook_config.ssl, request_generator, args.queryId, args.silent)

        print(json.dumps(res, indent=2))

    @cell_magic
    @display_exceptions
    def gremlin(self, line, cell):
        parser = argparse.ArgumentParser()
        parser.add_argument('query_mode', nargs='?', default='query',
                            help='query mode (default=query) [query|explain|profile]')
        parser.add_argument('-p', '--path-pattern', default='', help='path pattern')
        args = parser.parse_args(line.split())
        mode = str_to_query_mode(args.query_mode)

        tab = widgets.Tab()
        if mode == QueryMode.EXPLAIN:
            request_generator = create_request_generator(self.graph_notebook_config.auth_mode,
                                                         self.graph_notebook_config.iam_credentials_provider_type)
            raw_html = gremlin_explain(cell, self.graph_notebook_config.host, self.graph_notebook_config.port,
                                       self.graph_notebook_config.ssl, request_generator)
            explain_output = widgets.Output(layout=DEFAULT_LAYOUT)
            with explain_output:
                display(HTML(raw_html))
            tab.children = [explain_output]
            tab.set_title(0, 'Explain')
            display(tab)
        elif mode == QueryMode.PROFILE:
            request_generator = create_request_generator(self.graph_notebook_config.auth_mode,
                                                         self.graph_notebook_config.iam_credentials_provider_type)
            raw_html = gremlin_profile(cell, self.graph_notebook_config.host, self.graph_notebook_config.port,
                                       self.graph_notebook_config.ssl, request_generator)
            profile_output = widgets.Output(layout=DEFAULT_LAYOUT)
            with profile_output:
                display(HTML(raw_html))
            tab.children = [profile_output]
            tab.set_title(0, 'Profile')
            display(tab)
        else:
            client_provider = create_client_provider(self.graph_notebook_config.auth_mode,
                                                     self.graph_notebook_config.iam_credentials_provider_type)
            res = do_gremlin_query(cell, self.graph_notebook_config.host, self.graph_notebook_config.port,
                                   self.graph_notebook_config.ssl, client_provider)
            children = []
            titles = []

            table_output = widgets.Output(layout=DEFAULT_LAYOUT)
            titles.append('Console')
            children.append(table_output)

            try:
                gn = GremlinNetwork()
                if args.path_pattern == '':
                    gn.add_results(res)
                else:
                    pattern = parse_pattern_list_str(args.path_pattern)
                    gn.add_results_with_pattern(res, pattern)
                logger.debug(f'number of nodes is {len(gn.graph.nodes)}')
                if len(gn.graph.nodes) > 0:
                    f = Force(network=gn, options=self.graph_notebook_vis_options)
                    titles.append('Graph')
                    children.append(f)
                    logger.debug('added gremlin network to tabs')
            except ValueError as value_error:
                logger.debug(f'unable to create gremlin network from result. Skipping from result set: {value_error}')

            tab.children = children
            for i in range(len(titles)):
                tab.set_title(i, titles[i])
            display(tab)

            table_id = f"table-{str(uuid.uuid4()).replace('-', '')[:8]}"
            table_html = gremlin_table_template.render(guid=table_id, results=res)
            with table_output:
                display(HTML(table_html))

    @line_magic
    @display_exceptions
    def gremlin_status(self, line=''):
        parser = argparse.ArgumentParser()
        parser.add_argument('-q', '--queryId', default='',
                            help='The ID of a running Gremlin query. Only displays the status of the specified query.')
        parser.add_argument('-c', '--cancelQuery', action='store_true',
                            help='Required for cancellation. Parameter has no corresponding value.')
        parser.add_argument('-w', '--includeWaiting', action='store_true',
                            help='(Optional) Normally, only running queries are included in the response. When the includeWaiting parameter is specified, the status of all waiting queries is also returned.')
        args = parser.parse_args(line.split())

        request_generator = create_request_generator(self.graph_notebook_config.auth_mode,
                                                     self.graph_notebook_config.iam_credentials_provider_type)

        if not args.cancelQuery:
            res = do_gremlin_status(self.graph_notebook_config.host,
                                    self.graph_notebook_config.port,
                                    self.graph_notebook_config.ssl, self.graph_notebook_config.auth_mode,
                                    request_generator, args.queryId, args.includeWaiting)

        else:
            if args.queryId == '':
                print(GREMLIN_CANCEL_HINT_MSG)
                return
            else:
                res = do_gremlin_cancel(self.graph_notebook_config.host, self.graph_notebook_config.port,
                                        self.graph_notebook_config.ssl, self.graph_notebook_config.auth_mode,
                                        request_generator, args.queryId)

        print(json.dumps(res, indent=2))

    @line_magic
    @display_exceptions
    def status(self, line):
        logger.info(f'calling for status on endpoint {self.graph_notebook_config.host}')
        request_generator = create_request_generator(self.graph_notebook_config.auth_mode,
                                                     self.graph_notebook_config.iam_credentials_provider_type)
        logger.info(
            f'used credentials_provider_mode={self.graph_notebook_config.iam_credentials_provider_type.name} and auth_mode={self.graph_notebook_config.auth_mode.name} to make status request')

        res = get_status(self.graph_notebook_config.host, self.graph_notebook_config.port,
                         self.graph_notebook_config.ssl, request_generator)
        logger.info(f'got the response {res}')
        return res

    @line_magic
    @display_exceptions
    def db_reset(self, line):
        host = self.graph_notebook_config.host
        port = self.graph_notebook_config.port
        ssl = self.graph_notebook_config.ssl

        logger.info(f'calling system endpoint {host}')
        parser = argparse.ArgumentParser()
        parser.add_argument('-g', '--generate-token', action='store_true', help='generate token for database reset')
        parser.add_argument('-t', '--token', nargs=1, default='', help='perform database reset with given token')
        parser.add_argument('-y', '--yes', action='store_true', help='skip the prompt and perform database reset')
        args = parser.parse_args(line.split())
        generate_token = args.generate_token
        skip_prompt = args.yes
        request_generator = create_request_generator(self.graph_notebook_config.auth_mode,
                                                     self.graph_notebook_config.iam_credentials_provider_type)
        logger.info(
            f'used credentials_provider_mode={self.graph_notebook_config.iam_credentials_provider_type.name} and auth_mode={self.graph_notebook_config.auth_mode.name} to make system request')
        if generate_token is False and args.token == '':
            if skip_prompt:
                res = initiate_database_reset(host, port, ssl, request_generator)
                token = res['payload']['token']
                res = perform_database_reset(token, host, port, ssl, request_generator)
                logger.info(f'got the response {res}')
                return res

            output = widgets.Output()
            source = 'Are you sure you want to delete all the data in your cluster?'
            label = widgets.Label(source)
            text_hbox = widgets.HBox([label])
            check_box = widgets.Checkbox(
                value=False,
                disabled=False,
                indent=False,
                description='I acknowledge that upon deletion the cluster data will no longer be available.',
                layout=widgets.Layout(width='600px', margin='5px 5px 5px 5px')
            )
            button_delete = widgets.Button(description="Delete")
            button_cancel = widgets.Button(description="Cancel")
            button_hbox = widgets.HBox([button_delete, button_cancel])

            display(text_hbox, check_box, button_hbox, output)

            def on_button_delete_clicked(b):
                result = initiate_database_reset(host, port, ssl, request_generator)

                text_hbox.close()
                check_box.close()
                button_delete.close()
                button_cancel.close()
                button_hbox.close()

                if not check_box.value:
                    with output:
                        print('Checkbox is not checked.')
                    return
                token = result['payload']['token']
                if token == "":
                    with output:
                        print('Failed to get token.')
                        print(result)
                    return

                result = perform_database_reset(token, host, port, ssl, request_generator)

                if 'status' not in result or result['status'] != '200 OK':
                    with output:
                        print('Database reset failed, please try the operation again or reboot the cluster.')
                        print(result)
                        logger.error(result)
                    return

                retry = 10
                poll_interval = 5
                interval_output = widgets.Output()
                job_status_output = widgets.Output()
                status_hbox = widgets.HBox([interval_output])
                vbox = widgets.VBox([status_hbox, job_status_output])
                display(vbox)

                last_poll_time = time.time()
                while retry > 0:
                    time_elapsed = int(time.time() - last_poll_time)
                    time_remaining = poll_interval - time_elapsed
                    interval_output.clear_output()
                    if time_elapsed > poll_interval:
                        with interval_output:
                            print('checking status...')
                        job_status_output.clear_output()
                        with job_status_output:
                            display_html(HTML(loading_wheel_html))
                        try:
                            retry -= 1
                            interval_check_response = get_status(host, port, ssl, request_generator)
                        except Exception as e:
                            # Exception is expected when database is resetting, continue waiting
                            with job_status_output:
                                last_poll_time = time.time()
                                time.sleep(1)
                                continue
                        job_status_output.clear_output()
                        with job_status_output:
                            if interval_check_response["status"] == 'healthy':
                                interval_output.close()
                                print('Database has been reset.')
                                return
                        last_poll_time = time.time()
                    else:
                        with interval_output:
                            print(f'checking status in {time_remaining} seconds')
                    time.sleep(1)
                with output:
                    print(result)
                    if interval_check_response["status"] != 'healthy':
                        print("Could not retrieve the status of the reset operation within the allotted time. "
                              "If the database is not healthy after 1 min, please try the operation again or "
                              "reboot the cluster.")

            def on_button_cancel_clicked(b):
                text_hbox.close()
                check_box.close()
                button_delete.close()
                button_cancel.close()
                button_hbox.close()
                with output:
                    print('Database reset operation has been canceled.')

            button_delete.on_click(on_button_delete_clicked)
            button_cancel.on_click(on_button_cancel_clicked)
            return
        elif generate_token:
            res = initiate_database_reset(host, port, ssl, request_generator)
        else:
            # args.token is an array of a single string, e.g., args.token=['ade-23-c23'], use index 0 to take the string
            res = perform_database_reset(args.token[0], host, port, ssl, request_generator)

        logger.info(f'got the response {res}')
        return res

    @line_magic
    @display_exceptions
    def load(self, line):
        # since this can be a long-running task, freezing variables in the case
        # that a user alters them in another command.
        host = self.graph_notebook_config.host
        port = self.graph_notebook_config.port
        ssl = self.graph_notebook_config.ssl

        credentials_provider_mode = self.graph_notebook_config.iam_credentials_provider_type
        request_generator = create_request_generator(self.graph_notebook_config.auth_mode, credentials_provider_mode)
        load_role_arn = self.graph_notebook_config.load_from_s3_arn
        region = self.graph_notebook_config.aws_region

        button = widgets.Button(description="Submit")
        output = widgets.Output()
        source = widgets.Text(
            value='s3://',
            placeholder='Type something',
            description='Source:',
            disabled=False,
        )

        arn = widgets.Text(
            value=load_role_arn,
            placeholder='Type something',
            description='Load ARN:',
            disabled=False
        )

        source_format = widgets.Dropdown(
            options=['', 'csv', 'ntriples', 'nquads', 'rdfxml', 'turtle'],
            value='',  # blank so the user has to choose a format instead of risking the default one being incorrect.
            description='Format: ',
            disabled=False
        )

        region_box = widgets.Text(
            value=region,
            placeholder='us-east-1',
            description='AWS Region:',
            disabled=False
        )

        fail_on_error = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value='TRUE',
            description='Fail on Failure: ',
            disabled=False
        )

        parallelism = widgets.Dropdown(
            options=['LOW', 'MEDIUM', 'HIGH', 'OVERSUBSCRIBE'],
            value='HIGH',
            description='Parallelism :',
            disabled=False
        )

        update_single_cardinality = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value='FALSE',
            description='Update Single Cardinality:',
            disabled=False,
        )

        source_hbox = widgets.HBox([source])
        arn_hbox = widgets.HBox([arn])
        source_format_hbox = widgets.HBox([source_format])

        display(source_hbox, source_format_hbox, region_box, arn_hbox, fail_on_error, parallelism,
                 update_single_cardinality, button, output)

        def on_button_clicked(b):
            source_hbox.children = (source,)
            arn_hbox.children = (arn,)
            source_format_hbox.children = (source_format,)

            validated = True
            validation_label_style = DescriptionStyle(color='red')
            if not (source.value.startswith('s3://') and len(source.value) > 7) and not source.value.startswith('/'):
                validated = False
                source_validation_label = widgets.HTML(
                    '<p style="color:red;">Source must be an s3 bucket or file path</p>')
                source_validation_label.style = validation_label_style
                source_hbox.children += (source_validation_label,)

            if source_format.value == '':
                validated = False
                source_format_validation_label = widgets.HTML('<p style="color:red;">Format cannot be blank.</p>')
                source_format_hbox.children += (source_format_validation_label,)

            if not arn.value.startswith('arn:aws') and source.value.startswith(
                    "s3://"):  # only do this validation if we are using an s3 bucket.
                validated = False
                arn_validation_label = widgets.HTML('<p style="color:red;">Load ARN must start with "arn:aws"</p>')
                arn_hbox.children += (arn_validation_label,)

            if not validated:
                return

            source_exp = os.path.expandvars(
                source.value)  # replace any env variables in source.value with their values, can use $foo or ${foo}. Particularly useful for ${AWS_REGION}
            logger.info(f'using source_exp: {source_exp}')
            try:
                load_result = do_load(host, port, source_format.value, ssl, str(source_exp), region_box.value,
                                      arn.value,
                                      fail_on_error.value, parallelism.value, update_single_cardinality.value,
                                      request_generator)

                source_hbox.close()
                source_format_hbox.close()
                region_box.close()
                arn_hbox.close()
                fail_on_error.close()
                parallelism.close()
                update_single_cardinality.close()
                button.close()
                output.close()

                if 'status' not in load_result or load_result['status'] != '200 OK':
                    with output:
                        print('Something went wrong.')
                        print(load_result)
                        logger.error(load_result)
                    return

                load_id_label = widgets.Label(f'Load ID: {load_result["payload"]["loadId"]}')
                poll_interval = 5
                interval_output = widgets.Output()
                job_status_output = widgets.Output()

                load_id_hbox = widgets.HBox([load_id_label])
                status_hbox = widgets.HBox([interval_output])
                vbox = widgets.VBox([load_id_hbox, status_hbox, job_status_output])
                display(vbox)

                last_poll_time = time.time()
                while True:
                    time_elapsed = int(time.time() - last_poll_time)
                    time_remaining = poll_interval - time_elapsed
                    interval_output.clear_output()
                    if time_elapsed > poll_interval:
                        with interval_output:
                            print('checking status...')
                        job_status_output.clear_output()
                        with job_status_output:
                            display_html(HTML(loading_wheel_html))
                        try:
                            interval_check_response = get_load_status(host, port, ssl, request_generator,
                                                                      load_result['payload']['loadId'])
                        except Exception as e:
                            logger.error(e)
                            with job_status_output:
                                print('Something went wrong updating job status. Ending.')
                                return
                        job_status_output.clear_output()
                        with job_status_output:
                            print(f'Overall Status: {interval_check_response["payload"]["overallStatus"]["status"]}')
                            if interval_check_response["payload"]["overallStatus"]["status"] == 'LOAD_COMPLETED':
                                interval_output.close()
                                print('Done.')
                                return
                        last_poll_time = time.time()
                    else:
                        with interval_output:
                            print(f'checking status in {time_remaining} seconds')
                    time.sleep(1)
            except HTTPError as httpEx:
                output.clear_output()
                with output:
                    print(httpEx.response.content.decode('utf-8'))

        button.on_click(on_button_clicked)

    @line_magic
    @display_exceptions
    def load_ids(self, line):
        credentials_provider_mode = self.graph_notebook_config.iam_credentials_provider_type
        request_generator = create_request_generator(self.graph_notebook_config.auth_mode, credentials_provider_mode)
        res = get_loader_jobs(self.graph_notebook_config.host, self.graph_notebook_config.port,
                              self.graph_notebook_config.ssl, request_generator)
        ids = []
        if 'payload' in res and 'loadIds' in res['payload']:
            ids = res['payload']['loadIds']

        labels = [widgets.Label(value=label_id) for label_id in ids]

        if not labels:
            labels = [widgets.Label(value="No load IDs found.")]

        vbox = widgets.VBox(labels)
        display(vbox)

    @line_magic
    @display_exceptions
    def load_status(self, line):
        credentials_provider_mode = self.graph_notebook_config.iam_credentials_provider_type
        request_generator = create_request_generator(self.graph_notebook_config.auth_mode, credentials_provider_mode)
        res = get_load_status(self.graph_notebook_config.host, self.graph_notebook_config.port,
                              self.graph_notebook_config.ssl, request_generator, line)
        print(json.dumps(res, indent=2))

    @line_magic
    @display_exceptions
    def cancel_load(self, line):
        credentials_provider_mode = self.graph_notebook_config.iam_credentials_provider_type
        request_generator = create_request_generator(self.graph_notebook_config.auth_mode, credentials_provider_mode)
        res = cancel_load(self.graph_notebook_config.host, self.graph_notebook_config.port,
                          self.graph_notebook_config.ssl, request_generator, line)
        if res:
            print('Cancelled successfully.')
        else:
            print('Something went wrong cancelling bulk load job.')

    @line_magic
    def query_mode(self, line):
        self.mode = str_to_query_mode(line)
        print(f'Query mode set to {self.mode.value}')

    @line_magic
    @display_exceptions
    def seed(self, line):
        parser = argparse.ArgumentParser()
        parser.add_argument('--language', type=str, default='', choices=SEED_LANGUAGE_OPTIONS)
        parser.add_argument('--dataset', type=str, default='')
        parser.add_argument('--run', action='store_true')
        args = parser.parse_args(line.split())

        output = widgets.Output()
        progress_output = widgets.Output()
        language_dropdown = widgets.Dropdown(
            options=SEED_LANGUAGE_OPTIONS,
            description='Language:',
            disabled=False
        )

        data_set_drop_down = widgets.Dropdown(
            description='Data set:',
            disabled=False
        )

        submit_button = widgets.Button(description="Submit")
        data_set_drop_down.layout.visibility = 'hidden'
        submit_button.layout.visibility = 'hidden'

        def on_value_change(change):
            selected_language = change['new']
            data_sets = get_data_sets(selected_language)
            data_sets.sort()
            data_set_drop_down.options = [ds for ds in data_sets if
                                          ds != '__pycache__']  # being extra sure that we aren't passing __pycache__ here.
            data_set_drop_down.layout.visibility = 'visible'
            submit_button.layout.visibility = 'visible'
            return

        def on_button_clicked(b=None):
            submit_button.close()
            language_dropdown.disabled = True
            data_set_drop_down.disabled = True
            language = language_dropdown.value.lower()
            data_set = data_set_drop_down.value.lower()
            with output:
                print(f'Loading data set {data_set} with language {language}')
            queries = get_queries(language, data_set)
            if len(queries) < 1:
                with output:
                    print('Did not find any queries for the given dataset')
                return

            load_index = 1  # start at 1 to have a non-empty progress bar
            progress = widgets.IntProgress(
                value=load_index,
                min=0,
                max=len(queries) + 1,  # len + 1 so we can start at index 1
                orientation='horizontal',
                bar_style='info',
                description='Loading:'
            )

            with progress_output:
                display(progress)

            for q in queries:
                with output:
                    print(f'{progress.value}/{len(queries)}:\t{q["name"]}')
                # Just like with the load command, seed is long-running
                # as such, we want to obtain the values of host, port, etc. in case they
                # change during execution.
                host = self.graph_notebook_config.host
                port = self.graph_notebook_config.port
                auth_mode = self.graph_notebook_config.auth_mode
                ssl = self.graph_notebook_config.ssl

                if language == 'gremlin':
                    client_provider = create_client_provider(auth_mode,
                                                             self.graph_notebook_config.iam_credentials_provider_type)
                    # IMPORTANT: We treat each line as its own query!
                    for line in q['content'].splitlines():
                        try:
                            do_gremlin_query(line, host, port, ssl, client_provider)
                        except GremlinServerError as gremlinEx:
                            try:
                                error = json.loads(gremlinEx.args[0][5:])  # remove the leading error code.
                                content = json.dumps(error, indent=2)
                            except Exception:
                                content = {
                                    'error': gremlinEx
                                }

                            with output:
                                print(content)
                            progress.close()
                            return
                        except Exception as e:
                            content = {
                                'error': e
                            }
                            with output:
                                print(content)
                            progress.close()
                            return
                else:
                    request_generator = create_request_generator(auth_mode,
                                                                 self.graph_notebook_config.iam_credentials_provider_type)
                    try:
                        do_sparql_query(q['content'], host, port, ssl, request_generator)
                    except HTTPError as httpEx:
                        # attempt to turn response into json
                        try:
                            error = json.loads(httpEx.response.content.decode('utf-8'))
                            content = json.dumps(error, indent=2)
                        except Exception:
                            content = {
                                'error': httpEx
                            }
                        with output:
                            print(content)
                        progress.close()
                        return
                    except Exception as ex:
                        content = {
                            'error': str(ex)
                        }
                        with output:
                            print(content)

                        progress.close()
                        return

                progress.value += 1

            progress.close()
            with output:
                print('Done.')
            return

        submit_button.on_click(on_button_clicked)
        language_dropdown.observe(on_value_change, names='value')

        display(language_dropdown, data_set_drop_down, submit_button, progress_output, output)
        if args.language != '':
            language_dropdown.value = args.language

            if args.dataset != '' and args.dataset in data_set_drop_down.options:
                data_set_drop_down.value = args.dataset.lower()

                if args.run:
                    on_button_clicked()

    @line_magic
    def enable_debug(self, line):
        logger.setLevel(logging.DEBUG)

    @line_magic
    def disable_debug(self, line):
        logger.setLevel(logging.ERROR)

    @line_magic
    def graph_notebook_version(self, line):
        print(graph_notebook.__version__)

    @line_cell_magic
    @display_exceptions
    def graph_notebook_vis_options(self, line='', cell=''):
        if line == 'reset':
            self.graph_notebook_vis_options = OPTIONS_DEFAULT_DIRECTED

        if cell == '':
            print(json.dumps(self.graph_notebook_vis_options, indent=2))
        else:
            options_dict = json.loads(cell)
            self.graph_notebook_vis_options = vis_options_merge(self.graph_notebook_vis_options, options_dict)


def gremlin_explain(query, host, port, use_ssl, request_param_generator):
    result = do_gremlin_explain(query, host, port, use_ssl, request_param_generator)
    if 'explain' in result:
        html = pre_container_template.render(content=result['explain'])
    else:
        html = pre_container_template.render(content='No explain found')
    return html


def gremlin_profile(query, host, port, use_ssl, request_param_generator):
    result = do_gremlin_profile(query, host, port, use_ssl, request_param_generator)
    if 'profile' in result:
        html = pre_container_template.render(content=result['profile'])
    else:
        html = pre_container_template.render(content='No profile found')
    return html


def sparql_explain(query, host, port, use_ssl, request_param_generator=SPARQLRequestGenerator()):
    res = do_sparql_explain(query, host, port, use_ssl, request_param_generator)
    if 'error' in res:
        html = error_template.render(error=json.dumps(res['error'], indent=2))
    else:
        html = sparql_explain_template.render(table=res)

    return html
